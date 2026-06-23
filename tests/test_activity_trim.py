from __future__ import annotations

import numpy as np

from tdms_sync_checker.core import normalise_tdms_name, suggested_activity_trim, value_stats


def test_normalise_tdms_name_removes_trailing_multiline_metadata():
    assert normalise_tdms_name("Accumulator_Pressure_01\nextra metadata") == "Accumulator_Pressure_01"
    assert normalise_tdms_name("  M8_ShaftSpeedCAN  ") == "M8_ShaftSpeedCAN"


def test_value_stats_detects_constant_and_changing_signals():
    constant = value_stats(np.array([2.0, 2.0, 2.0]))
    changing = value_stats(np.array([0.0, 1.0, 2.0, np.nan]))

    assert constant["is_constant"] is True
    assert constant["is_changing"] is False
    assert changing["is_constant"] is False
    assert changing["is_changing"] is True
    assert changing["n_nan"] == 1
    assert changing["n_zero"] == 1


def test_suggested_activity_trim_detects_active_window():
    values = np.zeros(20)
    values[5:15] = 1.0

    trim = suggested_activity_trim(values)

    assert trim["activity_status"] == "activity detected"
    assert trim["suggested_first_active_index"] == 5
    assert trim["suggested_last_active_index"] == 14
    assert trim["suggested_samples_removed_start"] == 5
    assert trim["suggested_samples_removed_end"] == 5
    assert trim["suggested_samples_kept"] == 10


def test_suggested_activity_trim_handles_empty_constant_and_invalid_inputs():
    empty = suggested_activity_trim(np.array([]))
    constant = suggested_activity_trim(np.ones(8))
    invalid = suggested_activity_trim(np.array([np.nan, np.nan]))

    assert empty["activity_status"] == "empty"
    assert empty["suggested_samples_kept"] == 0

    assert constant["activity_status"] == "constant"
    assert constant["suggested_first_active_index"] == 0
    assert constant["suggested_last_active_index"] == 7

    assert invalid["activity_status"] == "all invalid"
    assert invalid["suggested_samples_removed_total"] == 2
