from __future__ import annotations

import pandas as pd

from tdms_sync_checker.core import between_group_sync, inside_group_sync


def _channel_scan_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "file": "sample.tdms",
                "file_name": "sample.tdms",
                "group": "Group 0",
                "channel": "A",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:00"),
                "reported_dt_s": 0.1,
                "raw_samples": 101,
                "raw_duration_s": 10.0,
                "is_constant": False,
                "is_changing": True,
                "mostly_zero": False,
            },
            {
                "file": "sample.tdms",
                "file_name": "sample.tdms",
                "group": "Group 0",
                "channel": "B",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:00"),
                "reported_dt_s": 0.1,
                "raw_samples": 101,
                "raw_duration_s": 10.0,
                "is_constant": True,
                "is_changing": False,
                "mostly_zero": False,
            },
            {
                "file": "sample.tdms",
                "file_name": "sample.tdms",
                "group": "Group 1",
                "channel": "C",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:01"),
                "reported_dt_s": 0.2,
                "raw_samples": 31,
                "raw_duration_s": 6.0,
                "is_constant": False,
                "is_changing": True,
                "mostly_zero": True,
            },
            {
                "file": "sample.tdms",
                "file_name": "sample.tdms",
                "group": "Group 1",
                "channel": "D",
                "reported_start_time": pd.Timestamp("2026-01-01T00:00:01"),
                "reported_dt_s": 0.2,
                "raw_samples": 30,
                "raw_duration_s": 5.8,
                "is_constant": False,
                "is_changing": True,
                "mostly_zero": False,
            },
        ]
    )


def test_inside_group_sync_reports_consistency_and_mismatches():
    report = inside_group_sync(_channel_scan_frame()).set_index("group")

    assert bool(report.loc["Group 0", "same_start_time"]) is True
    assert bool(report.loc["Group 0", "same_dt"]) is True
    assert bool(report.loc["Group 0", "same_samples"]) is True
    assert int(report.loc["Group 0", "n_constant_channels"]) == 1

    assert bool(report.loc["Group 1", "same_start_time"]) is True
    assert bool(report.loc["Group 1", "same_dt"]) is True
    assert bool(report.loc["Group 1", "same_samples"]) is False
    assert int(report.loc["Group 1", "n_mostly_zero_channels"]) == 1


def test_between_group_sync_estimates_offsets_and_common_overlap():
    report = between_group_sync(_channel_scan_frame()).set_index("group")

    assert report.loc["Group 0", "offset_from_earliest_group_s"] == 0.0
    assert report.loc["Group 1", "offset_from_earliest_group_s"] == 1.0
    assert report.loc["Group 0", "group_sample_rate_hz"] == 10.0
    assert report.loc["Group 1", "group_sample_rate_hz"] == 5.0

    # Group 0 spans 0--10 s and Group 1 spans 1--7 s, so the common overlap is 6 s.
    assert report["common_overlap_duration_s"].min() == 6.0
