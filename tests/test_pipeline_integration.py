from __future__ import annotations

from pathlib import Path

import pandas as pd


def _fake_scan_tdms_file(path: Path, log_func=print):
    del log_func

    channel_scan = pd.DataFrame(
        [
            {
                "file": str(path),
                "file_name": path.name,
                "group": "Group 0",
                "channel": "Accumulator_Pressure_01",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:00"),
                "reported_dt_s": 0.1,
                "reported_sample_rate_hz": 10.0,
                "raw_samples": 101,
                "raw_duration_s": 10.0,
                "min_value": 0.0,
                "max_value": 1.0,
                "mean_value": 0.5,
                "std_value": 0.1,
                "range_value": 1.0,
                "n_nan": 0,
                "n_zero": 1,
                "zero_percent": 1.0,
                "is_constant": False,
                "is_changing": True,
                "mostly_zero": False,
            },
            {
                "file": str(path),
                "file_name": path.name,
                "group": "Group 1",
                "channel": "M8_ShaftSpeedCAN",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:00"),
                "reported_dt_s": 0.1,
                "reported_sample_rate_hz": 10.0,
                "raw_samples": 101,
                "raw_duration_s": 10.0,
                "min_value": 10.0,
                "max_value": 20.0,
                "mean_value": 15.0,
                "std_value": 1.0,
                "range_value": 10.0,
                "n_nan": 0,
                "n_zero": 0,
                "zero_percent": 0.0,
                "is_constant": False,
                "is_changing": True,
                "mostly_zero": False,
            },
        ]
    )

    suggested_trim = pd.DataFrame(
        [
            {
                "file": str(path),
                "file_name": path.name,
                "group": "Group 0",
                "channel": "Accumulator_Pressure_01",
                "raw_samples": 101,
                "suggested_first_active_index": 0,
                "suggested_last_active_index": 100,
                "suggested_samples_removed_start": 0,
                "suggested_samples_removed_end": 0,
                "suggested_samples_kept": 101,
                "suggested_samples_removed_total": 0,
                "activity_status": "activity detected",
            },
            {
                "file": str(path),
                "file_name": path.name,
                "group": "Group 1",
                "channel": "M8_ShaftSpeedCAN",
                "raw_samples": 101,
                "suggested_first_active_index": 0,
                "suggested_last_active_index": 100,
                "suggested_samples_removed_start": 0,
                "suggested_samples_removed_end": 0,
                "suggested_samples_kept": 101,
                "suggested_samples_removed_total": 0,
                "activity_status": "activity detected",
            },
        ]
    )

    return channel_scan, suggested_trim


def test_run_analysis_writes_expected_reports_with_mocked_tdms_scan(tmp_path, monkeypatch):
    from tdms_sync_checker import core

    input_dir = tmp_path / "tdms_input"
    output_dir = tmp_path / "tdms_output"
    input_dir.mkdir()
    tdms_path = input_dir / "test_run_001.tdms"
    tdms_path.write_bytes(b"synthetic placeholder; scan is monkeypatched")

    monkeypatch.setattr(core, "scan_tdms_file", _fake_scan_tdms_file)

    result, excel_path, html_path, summary_text = core.run_analysis(
        input_dir,
        output_dir,
        log_func=lambda _message: None,
    )

    assert result["channel_scan"].shape[0] == 2
    assert result["inside_group"].shape[0] == 2
    assert result["between_group"].shape[0] == 2
    assert "Files analysed: 1" in summary_text

    assert (output_dir / "summary.txt").exists()
    assert excel_path.exists()
    assert html_path.exists()
    assert (output_dir / "csv" / "channel_metadata_all_channels.csv").exists()
    assert (output_dir / "csv" / "inside_group_sync.csv").exists()
    assert (output_dir / "csv" / "between_group_sync.csv").exists()
    assert (output_dir / "csv" / "split_file_continuity.csv").exists()
    assert (output_dir / "csv" / "suggested_activity_trim.csv").exists()
