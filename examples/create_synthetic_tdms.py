"""Create a small public-safe synthetic TDMS file for repository examples.

The generated file imitates useful TDMS metadata patterns without copying real
laboratory data. It is intended for README examples, smoke checks, and manual
review of the TDMS Sync Checker workflow.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from nptdms import ChannelObject, GroupObject, RootObject, TdmsWriter

OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "synthetic_tdms_reference.tdms"
BASE_START = np.datetime64("2024-01-01T12:00:00.000000")


def _start(offset_s: float) -> np.datetime64:
    """Return a TDMS-compatible timestamp offset from the synthetic start time."""
    offset_us = int(round(offset_s * 1_000_000))
    return BASE_START + np.timedelta64(offset_us, "us")


def _time(n_samples: int, dt: float) -> np.ndarray:
    return np.arange(n_samples, dtype=np.float64) * dt


def _props(channel_name: str, unit: str, dt: float, n_samples: int, start_offset_s: float) -> dict:
    return {
        "wf_start_time": _start(start_offset_s),
        "wf_start_offset": 0.0,
        "wf_increment": float(dt),
        "wf_samples": int(n_samples),
        "NI_ChannelName": channel_name,
        "NI_UnitDescription": unit,
        "unit_string": unit,
    }


def _wave(n_samples: int, dt: float, base: float, amplitude: float, period_s: float, phase: float = 0.0) -> np.ndarray:
    t = _time(n_samples, dt)
    return base + amplitude * np.sin(2.0 * np.pi * t / period_s + phase)


def _square_command(n_samples: int, dt: float, period_s: float = 0.70) -> np.ndarray:
    t = _time(n_samples, dt)
    return np.where((t % period_s) < (0.5 * period_s), 1.0, -1.0)


def _timestamp_channel(n_samples: int, dt: float) -> np.ndarray:
    return _time(n_samples, dt)


def _channel(group: str, name: str, values: np.ndarray, unit: str, dt: float, start_offset_s: float) -> ChannelObject:
    return ChannelObject(
        group,
        name,
        np.asarray(values, dtype=np.float64),
        properties=_props(name, unit, dt, len(values), start_offset_s),
    )


def _timestamp(group: str, name: str, n_samples: int, dt: float) -> ChannelObject:
    # Intentionally omit waveform properties to imitate timestamp columns that
    # are data channels rather than standard waveform channels.
    return ChannelObject(group, name, _timestamp_channel(n_samples, dt))


def _constant_channel(group: str, name: str, n_samples: int, value: float = 0.0) -> ChannelObject:
    # Intentionally awkward metadata: present but uninformative channel.
    return ChannelObject(
        group,
        name,
        np.full(n_samples, value, dtype=np.float64),
        properties={
            "wf_start_time": np.datetime64("1904-01-01T00:00:00.000000"),
            "wf_start_offset": 0.0,
            "wf_increment": 1.0,
            "wf_samples": int(n_samples),
        },
    )


def build_synthetic_channels() -> list:
    """Build TDMS root, group, and channel objects for one synthetic file."""
    objects: list = [
        RootObject(
            properties={
                "title": "Synthetic TDMS reference file",
                "description": "Public-safe synthetic data for tdms-sync-checker examples.",
            }
        )
    ]

    groups = [
        "0_cRIO_Control_Pressure",
        "6_CAN_DDP",
        "1_cDAQ_DDP_Pressure",
        "2_cDAQ_Control_Load_Position_Pressure",
        "3_cDAQ_Motion_Temp_Strain",
        "8_DIC_Trigger_Pulse",
    ]
    objects.extend(GroupObject(group) for group in groups)

    # Group 0: higher-rate pressure/control channels.
    group = "0_cRIO_Control_Pressure"
    n, dt, offset = 6000, 0.01, 0.241807
    objects.extend(
        [
            _channel(group, "Accumulator_Pressure_01", _wave(n, dt, 105.0, 12.0, 6.0), "Bar", dt, offset),
            _channel(group, "Accumulator_Pressure_02", _wave(n, dt, 104.0, 11.5, 6.0, 0.2), "Bar", dt, offset),
            _channel(group, "DDP_Tank_Level", _wave(n, dt, 780.0, 5.0, 30.0), "mm", dt, offset),
            _channel(group, "DDP_LP_Flow_Rate", _wave(n, dt, 45.0, 6.0, 4.0), "l/min", dt, offset),
            _channel(group, "DDP_Boost_Pump_Pressure_01", _wave(n, dt, 18.0, 2.0, 5.0), "Bar", dt, offset),
            _constant_channel(group, "Untitled 7", n),
            _timestamp(group, "Time Stamp_Group_0_cRIO_Control_Pressure", n, dt),
        ]
    )

    # Group 1: CAN-style channels with newline suffixes.
    group = "6_CAN_DDP"
    n, dt, offset = 1000, 0.05, 0.666143
    cmd = _square_command(n, dt)
    objects.extend(
        [
            _channel(group, "M8_ShaftSpeed\nCAN_Database_Master_2", 720.0 + 80.0 * cmd, "RPM", dt, offset),
            _channel(group, "M7_ShaftSpeed\nCAN_Database_Master_2", 705.0 + 75.0 * cmd, "RPM", dt, offset),
            _channel(
                group, "M8_Temperature\nCAN_Database_Master_2", _wave(n, dt, 38.0, 1.5, 35.0), "Deg C", dt, offset
            ),
            _channel(
                group, "M7_Temperature\nCAN_Database_Master_2", _wave(n, dt, 37.0, 1.2, 38.0), "Deg C", dt, offset
            ),
            _channel(group, "M8S8_PressureActual\nCAN_Database_Master_2", 145.0 + 20.0 * cmd, "Bar", dt, offset),
            _channel(group, "M7S7_PressureActual\nCAN_Database_Master_2", 142.0 + 18.0 * cmd, "Bar", dt, offset),
            _channel(group, "M8S8_FdLimited\nCAN_Database_Master_2", cmd, "Command", dt, offset),
            _channel(group, "M7S7_FdLimited\nCAN_Database_Master_2", cmd, "Command", dt, offset),
            _timestamp(group, "Time Stamp_Group_6_CAN_DDP", n, dt),
        ]
    )

    # Group 2: DDP pressure and temperature.
    group = "1_cDAQ_DDP_Pressure"
    n, dt, offset = 1000, 0.05, 0.685305
    objects.extend(
        [
            _channel(group, "DDP_Pressure_HP_01", 165.0 + 24.0 * cmd, "Bar", dt, offset),
            _channel(group, "DDP_Pressure_HP_02", 162.0 + 22.0 * cmd, "Bar", dt, offset),
            _channel(group, "DDP_Pressure_LP_01", _wave(n, dt, 24.0, 3.0, 7.0), "Bar", dt, offset),
            _channel(group, "DDP_Pressure_LP_02", _wave(n, dt, 23.5, 2.5, 7.5), "Bar", dt, offset),
            _channel(group, "Actuator_A_01_Oil_Temperature", _wave(n, dt, 41.0, 1.0, 45.0), "Deg C", dt, offset),
            _timestamp(group, "Time Stamp_Group_1_cDAQ_DDP_Pressure", n, dt),
        ]
    )

    # Group 3: load, position, and pressure.
    group = "2_cDAQ_Control_Load_Position_Pressure"
    n, dt, offset = 1000, 0.05, 1.578897
    objects.extend(
        [
            _channel(group, "Actuator_Load_A_01", _wave(n, dt, 5.0, 120.0, 2.0), "kN", dt, offset),
            _channel(group, "Actuator_Load_B_01", _wave(n, dt, -5.0, 118.0, 2.0, 0.1), "kN", dt, offset),
            _channel(group, "Actuator_Position_A_01", _wave(n, dt, 0.0, 8.0, 2.0), "mm", dt, offset),
            _channel(group, "Actuator_Position_B_01", _wave(n, dt, 0.2, 7.8, 2.0, 0.1), "mm", dt, offset),
            _channel(group, "Actuator_Pressure_A_01", _wave(n, dt, 135.0, 14.0, 2.0), "Bar", dt, offset),
            _channel(group, "Actuator_Pressure_B_01", _wave(n, dt, 132.0, 14.0, 2.0, 0.1), "Bar", dt, offset),
            _constant_channel(group, "Untitled 16", n),
            _timestamp(group, "Time Stamp_Group_2_cDAQ_Control_Load_Position_Pressure", n, dt),
        ]
    )

    # Group 4: motion, temperature, power, acceleration, and strain subset.
    group = "3_cDAQ_Motion_Temp_Strain"
    n, dt, offset = 1000, 0.05, 1.700089
    delayed_cmd = np.roll(cmd, 3)
    objects.extend(
        [
            _channel(group, "DDP_Inverter_Power_01", 35.0 + 12.0 * delayed_cmd, "kW", dt, offset),
            _channel(group, "DDP_Inverter_Power_02", 32.0 + 10.0 * delayed_cmd, "kW", dt, offset),
            _channel(group, "Temp_External_Ambient_Air", _wave(n, dt, 18.0, 0.5, 60.0), "Deg C", dt, offset),
            _channel(group, "Temp_Flow_01", _wave(n, dt, 42.0, 1.8, 35.0), "Deg C", dt, offset),
            _channel(group, "Acc_R_NE_X", _wave(n, dt, 0.0, 0.05, 0.5), "G", dt, offset),
            _channel(group, "Acc_R_NE_Y", _wave(n, dt, 0.0, 0.04, 0.45), "G", dt, offset),
            _channel(group, "Inc_1_x", _wave(n, dt, 0.1, 0.02, 10.0), "Degrees", dt, offset),
            _channel(
                group, "Str_Lin_Frame_Internal_Axial_01", _wave(n, dt, 50.0, 30.0, 2.0), "microstrain", dt, offset
            ),
            _timestamp(group, "Time Stamp_Group_3_cDAQ_Motion_Temp_Strain", n, dt),
        ]
    )

    # Group 5: lower-rate trigger pulse.
    group = "8_DIC_Trigger_Pulse"
    n, dt, offset = 500, 0.10, 0.0
    trigger = np.zeros(n, dtype=np.float64)
    trigger[25::50] = 1.0
    objects.extend(
        [
            _channel(group, "Digital_Trigger_1", trigger, "Binary", dt, offset),
            _timestamp(group, "Time Stamp_Group_8_DIC_Trigger_Pulse", n, dt),
        ]
    )

    return objects


def create_synthetic_tdms(output_path: Path = OUTPUT_PATH) -> Path:
    """Write the synthetic TDMS file and return its path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with TdmsWriter(output_path) as writer:
        writer.write_segment(build_synthetic_channels())

    return output_path


def main() -> None:
    output_path = create_synthetic_tdms()
    print(f"Synthetic TDMS file written to: {output_path}")


if __name__ == "__main__":
    main()
