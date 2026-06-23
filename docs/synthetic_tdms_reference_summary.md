# Synthetic TDMS reference summary

This document explains the public-safe TDMS metadata pattern used by `examples/create_synthetic_tdms.py`.

## Purpose

The synthetic TDMS file is designed to make the repository easier to review without committing real laboratory data. It gives users a small file that exercises the main metadata-first workflow:

- multiple TDMS groups;
- mixed sampling intervals;
- group start-time offsets;
- timestamp-like channels;
- CAN-style channel names with newline suffixes;
- changing, constant, and mostly-zero channels;
- inactive/awkward metadata cases;
- command-response-style signals useful for future diagnostics.

## Pattern used

The uploaded reference file was used only to identify broad metadata patterns. The synthetic generator does **not** copy the measured data.

The reference pattern contained:

| Pattern | Public-safe synthetic equivalent |
|---|---|
| Several acquisition groups | Six synthetic groups with similar naming style |
| Mixed sample intervals | 0.01 s, 0.05 s, and 0.10 s groups |
| Timestamp channels | Numeric timestamp-style channels with no waveform metadata |
| CAN channels with newline suffixes | Synthetic CAN-style channels such as `M8_ShaftSpeed\nCAN_Database_Master_2` |
| Inactive/untitled channels | Constant `Untitled` channels to exercise metadata edge cases |
| Command-like channels | Synthetic `FdLimited` square-wave commands |
| Power/pressure/load/temperature-like channels | Smooth synthetic signals with noise-free illustrative behaviour |

## Generated groups

The script generates a small file with these groups:

```text
0_cRIO_Control_Pressure
6_CAN_DDP
1_cDAQ_DDP_Pressure
2_cDAQ_Control_Load_Position_Pressure
3_cDAQ_Motion_Temp_Strain
8_DIC_Trigger_Pulse
```

The names are intentionally similar to engineering acquisition group names so that the checker is exercised on realistic metadata structure, while the values remain synthetic.

## Generated output

Run:

```powershell
python examples/create_synthetic_tdms.py
```

This writes:

```text
examples/data/synthetic_tdms_reference.tdms
```

Then run:

```powershell
tdms-sync-checker `
  --input "examples/data/synthetic_tdms_reference.tdms" `
  --output "examples/outputs/synthetic_tdms_reference"
```

## Important limitation

The synthetic file is intended for software demonstration and QA/QC workflow testing. It is not a physical model of a facility, not a validated acquisition simulation, and not a replacement for validation against real hardware behaviour.
