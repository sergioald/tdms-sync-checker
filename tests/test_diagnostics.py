from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tdms_sync_checker.diagnostics import (
    build_diagnostic_summary,
    build_time_axis,
    detect_edges,
    estimate_active_window,
    estimate_common_active_window,
    estimate_cycles_from_edges,
    estimate_threshold,
    match_response_delays,
    summarise_cycle_stability,
    summarise_delay_drift,
)


def test_build_time_axis_from_dt():
    time_s = build_time_axis(5, dt_s=0.25)
    np.testing.assert_allclose(time_s, [0.0, 0.25, 0.5, 0.75, 1.0])


def test_build_time_axis_validates_length():
    with pytest.raises(ValueError):
        build_time_axis(3, time_values=[0.0, 1.0])


def test_estimate_threshold_for_binary_signal():
    y = np.array([0, 0, 0, 1, 1, 1], dtype=float)
    assert estimate_threshold(y) == pytest.approx(0.5)


def test_detect_rising_edges_binary_command():
    time_s = np.arange(10, dtype=float)
    command = np.array([0, 0, 1, 1, 0, 0, 1, 1, 0, 0], dtype=float)

    edges = detect_edges(time_s, command, threshold=0.5, direction="rising")

    assert list(edges["sample_index"]) == [2, 6]
    assert list(edges["time_s"]) == [2.0, 6.0]
    assert list(edges["edge_type"]) == ["rising", "rising"]


def test_detect_edges_min_interval_suppresses_close_crossing():
    time_s = np.arange(8, dtype=float)
    command = np.array([0, 1, 0, 1, 0, 0, 1, 1], dtype=float)

    edges = detect_edges(time_s, command, threshold=0.5, direction="rising", min_interval_s=3.0)

    assert list(edges["sample_index"]) == [1, 6]


def test_estimate_cycles_from_edges():
    edges = pd.DataFrame(
        {
            "event_index": [1, 2, 3],
            "sample_index": [10, 20, 30],
            "time_s": [1.0, 2.5, 4.0],
            "edge_type": ["rising", "rising", "rising"],
            "threshold": [0.5, 0.5, 0.5],
            "value_before": [0.0, 0.0, 0.0],
            "value_after": [1.0, 1.0, 1.0],
        }
    )

    cycles = estimate_cycles_from_edges(edges)

    assert len(cycles) == 2
    np.testing.assert_allclose(cycles["duration_s"], [1.5, 1.5])


def test_summarise_cycle_stability():
    cycles = pd.DataFrame({"duration_s": [10.0, 10.1, 9.9, 10.0]})
    summary = summarise_cycle_stability(cycles)

    assert summary["n_cycles"] == 4
    assert summary["median_duration_s"] == pytest.approx(10.0)
    assert summary["max_abs_deviation_from_median_s"] == pytest.approx(0.1)


def test_match_response_delays():
    command_edges = pd.DataFrame(
        {
            "event_index": [1, 2, 3],
            "sample_index": [10, 20, 30],
            "time_s": [1.0, 3.0, 5.0],
            "edge_type": ["rising", "rising", "rising"],
            "threshold": [0.5, 0.5, 0.5],
            "value_before": [0.0, 0.0, 0.0],
            "value_after": [1.0, 1.0, 1.0],
        }
    )
    response_edges = pd.DataFrame(
        {
            "event_index": [1, 2, 3],
            "sample_index": [11, 21, 31],
            "time_s": [1.2, 3.25, 5.3],
            "edge_type": ["rising", "rising", "rising"],
            "threshold": [0.5, 0.5, 0.5],
            "value_before": [0.0, 0.0, 0.0],
            "value_after": [1.0, 1.0, 1.0],
        }
    )

    delays = match_response_delays(command_edges, response_edges, max_delay_s=1.0)

    assert delays["matched"].tolist() == [True, True, True]
    np.testing.assert_allclose(delays["delay_s"], [0.2, 0.25, 0.3])


def test_match_response_delays_respects_max_delay():
    command_edges = pd.DataFrame(
        {
            "event_index": [1],
            "sample_index": [10],
            "time_s": [1.0],
            "edge_type": ["rising"],
            "threshold": [0.5],
            "value_before": [0.0],
            "value_after": [1.0],
        }
    )
    response_edges = pd.DataFrame(
        {
            "event_index": [1],
            "sample_index": [20],
            "time_s": [5.0],
            "edge_type": ["rising"],
            "threshold": [0.5],
            "value_before": [0.0],
            "value_after": [1.0],
        }
    )

    delays = match_response_delays(command_edges, response_edges, max_delay_s=1.0)

    assert delays.loc[0, "matched"] is False or delays.loc[0, "matched"] == np.False_
    assert np.isnan(delays.loc[0, "delay_s"])


def test_summarise_delay_drift_positive_slope():
    delays = pd.DataFrame(
        {
            "matched": [True, True, True, True],
            "command_time_s": [0.0, 10.0, 20.0, 30.0],
            "delay_s": [0.1, 0.2, 0.3, 0.4],
        }
    )

    summary = summarise_delay_drift(delays)

    assert summary["n_matches"] == 4
    assert summary["delay_drift_s_per_cycle"] > 0
    assert summary["delay_drift_s_per_second"] > 0


def test_estimate_active_window_detects_activity_region():
    time_s = np.arange(10, dtype=float)
    values = np.array([0, 0, 0, 2, 2, 2, 2, 0, 0, 0], dtype=float)

    window = estimate_active_window(time_s, values)

    assert window["activity_status"] == "activity detected"
    assert window["first_active_time_s"] == pytest.approx(3.0)
    assert window["last_active_time_s"] == pytest.approx(6.0)


def test_estimate_common_active_window_overlap():
    windows = pd.DataFrame(
        {
            "first_active_time_s": [1.0, 2.0, 0.5],
            "last_active_time_s": [9.0, 8.0, 7.0],
        }
    )

    common = estimate_common_active_window(windows)

    assert common["common_active_status"] == "overlap"
    assert common["common_active_start_s"] == pytest.approx(2.0)
    assert common["common_active_end_s"] == pytest.approx(7.0)
    assert common["common_active_duration_s"] == pytest.approx(5.0)


def test_build_diagnostic_summary_to_text():
    command_edges = detect_edges([0, 1, 2, 3], [0, 1, 0, 1], threshold=0.5, direction="rising")
    response_edges = detect_edges([0, 1, 2, 3], [0, 0, 1, 0], threshold=0.5, direction="rising")
    cycles = estimate_cycles_from_edges(command_edges)
    delays = match_response_delays(command_edges, response_edges, max_delay_s=2.0)

    summary = build_diagnostic_summary(command_edges, response_edges, cycles, delays)
    text = summary.to_text()

    assert "ENGINEERING DIAGNOSTIC SUMMARY" in text
    assert summary.n_command_edges == 2
