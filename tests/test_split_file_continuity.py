from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tdms_sync_checker.core import infer_test_id, split_file_continuity


def test_infer_test_id_removes_numeric_split_suffix():
    assert infer_test_id(Path("experiment_001.tdms")) == "experiment"
    assert infer_test_id(Path("experiment-002.tdms")) == "experiment"
    assert infer_test_id(Path("experiment_section_a.tdms")) == "experiment_section_a"


def test_split_file_continuity_classifies_first_continuous_gap_and_overlap():
    paths = [
        Path("run_001.tdms"),
        Path("run_002.tdms"),
        Path("run_003.tdms"),
        Path("run_004.tdms"),
    ]

    starts = [
        pd.Timestamp("2026-01-01T00:00:00.0"),
        pd.Timestamp("2026-01-01T00:00:10.2"),
        pd.Timestamp("2026-01-01T00:00:20.8"),
        pd.Timestamp("2026-01-01T00:00:22.0"),
    ]
    durations = [10.0, 5.0, 3.0, 3.0]

    rows = []
    for path, start, duration in zip(paths, starts, durations, strict=True):
        rows.append(
            {
                "file": str(path),
                "file_name": path.name,
                "group": "Group 0",
                "channel": "A",
                "reported_start_time": start,
                "raw_duration_s": duration,
            }
        )

    report = split_file_continuity(paths, pd.DataFrame(rows))

    assert report["section_status"].tolist() == ["first section", "continuous", "gap", "overlap"]
    assert report["section_number"].tolist() == [1, 2, 3, 4]
    assert report.loc[1, "gap_from_previous_s"] == pytest.approx(0.2)
    assert report.loc[2, "gap_from_previous_s"] > 0.5
    assert report.loc[3, "gap_from_previous_s"] < 0.0
