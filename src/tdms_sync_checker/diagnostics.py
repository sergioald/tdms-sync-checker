"""Optional signal-level engineering diagnostics for TDMS synchronisation review.

The core package remains metadata-first. This module provides conservative,
standalone helpers for analysing selected command/response channels after the
user has identified the channels of interest.

The functions are intentionally written around NumPy arrays and pandas tables so
that they can be tested without shipping real TDMS data.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DiagnosticSummary:
    """Small text summary produced by engineering-diagnostic scripts."""

    n_command_edges: int
    n_response_edges: int
    n_cycles: int
    n_matched_delays: int
    median_cycle_duration_s: float
    median_response_delay_s: float
    delay_drift_s_per_cycle: float

    def to_text(self) -> str:
        """Return a human-readable text summary."""
        lines = [
            "ENGINEERING DIAGNOSTIC SUMMARY",
            "=" * 70,
            f"Command edges detected: {self.n_command_edges}",
            f"Response edges detected: {self.n_response_edges}",
            f"Cycles estimated: {self.n_cycles}",
            f"Matched command-response delays: {self.n_matched_delays}",
            f"Median cycle duration: {_fmt_float(self.median_cycle_duration_s)} s",
            f"Median response delay: {_fmt_float(self.median_response_delay_s)} s",
            f"Delay drift: {_fmt_float(self.delay_drift_s_per_cycle)} s/cycle",
            "",
            "Interpretation notes:",
            "- Edge detection is threshold based and should be reviewed visually.",
            "- Delay estimates depend on the selected command/response channels.",
            "- These diagnostics support engineering review; they do not prove synchronisation by themselves.",
        ]
        return "\n".join(lines)


def _fmt_float(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "n/a"
    return f"{float(value):.6g}"


def as_1d_float_array(values: Iterable[float]) -> np.ndarray:
    """Convert input values to a finite-friendly one-dimensional float array."""
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        arr = np.ravel(arr)
    return arr


def build_time_axis(
    n_samples: int,
    dt_s: float | None = None,
    start_s: float = 0.0,
    time_values: Iterable[float] | None = None,
) -> np.ndarray:
    """Build or validate a time axis in seconds.

    Parameters
    ----------
    n_samples:
        Number of samples expected in the signal.
    dt_s:
        Constant sampling interval in seconds. Used when ``time_values`` is not
        provided.
    start_s:
        Start time in seconds for generated axes.
    time_values:
        Optional explicit time vector. If supplied, it must have ``n_samples``
        values.
    """
    if n_samples < 0:
        raise ValueError("n_samples must be non-negative")

    if time_values is not None:
        time_s = as_1d_float_array(time_values)
        if len(time_s) != n_samples:
            raise ValueError("time_values length must match n_samples")
        return time_s

    if dt_s is None or not np.isfinite(dt_s) or dt_s <= 0:
        raise ValueError("dt_s must be a positive finite value when time_values is not provided")

    return start_s + np.arange(n_samples, dtype=float) * float(dt_s)


def estimate_threshold(
    values: Iterable[float],
    lower_quantile: float = 0.05,
    upper_quantile: float = 0.95,
) -> float:
    """Estimate a robust mid-level threshold for a command or response signal.

    The threshold is the midpoint between low and high quantiles. This works well
    for binary command channels and many event-like response channels. Constant
    or all-invalid channels return ``nan``.
    """
    y = as_1d_float_array(values)
    finite = y[np.isfinite(y)]

    if len(finite) == 0:
        return np.nan

    low = float(np.quantile(finite, lower_quantile))
    high = float(np.quantile(finite, upper_quantile))

    if np.isclose(low, high):
        return np.nan

    return 0.5 * (low + high)


def detect_edges(
    time_s: Iterable[float],
    values: Iterable[float],
    threshold: float | None = None,
    direction: str = "rising",
    min_interval_s: float = 0.0,
) -> pd.DataFrame:
    """Detect threshold-crossing edges in a selected channel.

    Parameters
    ----------
    time_s, values:
        Equal-length one-dimensional arrays.
    threshold:
        Threshold to use. If ``None``, a robust threshold is estimated from the
        values.
    direction:
        ``"rising"``, ``"falling"``, or ``"both"``.
    min_interval_s:
        Minimum accepted time separation between returned edges. This is useful
        for suppressing double detections from noisy threshold crossings.
    """
    direction = direction.lower().strip()
    if direction not in {"rising", "falling", "both"}:
        raise ValueError("direction must be 'rising', 'falling', or 'both'")

    t = as_1d_float_array(time_s)
    y = as_1d_float_array(values)

    if len(t) != len(y):
        raise ValueError("time_s and values must have the same length")

    if len(y) < 2:
        return _empty_edges(threshold if threshold is not None else np.nan)

    if threshold is None:
        threshold = estimate_threshold(y)

    if threshold is None or not np.isfinite(threshold):
        return _empty_edges(np.nan)

    finite_pair = np.isfinite(t[:-1]) & np.isfinite(t[1:]) & np.isfinite(y[:-1]) & np.isfinite(y[1:])
    above = y >= float(threshold)

    rising_idx = np.where(finite_pair & (~above[:-1]) & above[1:])[0] + 1
    falling_idx = np.where(finite_pair & above[:-1] & (~above[1:]))[0] + 1

    rows = []
    if direction in {"rising", "both"}:
        rows.extend((idx, "rising") for idx in rising_idx)
    if direction in {"falling", "both"}:
        rows.extend((idx, "falling") for idx in falling_idx)

    rows.sort(key=lambda item: (float(t[item[0]]), item[0]))

    filtered = []
    last_time = -np.inf
    min_interval_s = max(0.0, float(min_interval_s))
    for idx, edge_type in rows:
        edge_time = float(t[idx])
        if edge_time - last_time + 1e-12 < min_interval_s:
            continue
        filtered.append((idx, edge_type))
        last_time = edge_time

    out = []
    for event_index, (idx, edge_type) in enumerate(filtered, start=1):
        out.append(
            {
                "event_index": event_index,
                "sample_index": int(idx),
                "time_s": float(t[idx]),
                "edge_type": edge_type,
                "threshold": float(threshold),
                "value_before": float(y[idx - 1]),
                "value_after": float(y[idx]),
            }
        )

    return pd.DataFrame(out, columns=_edge_columns())


def _edge_columns() -> list[str]:
    return [
        "event_index",
        "sample_index",
        "time_s",
        "edge_type",
        "threshold",
        "value_before",
        "value_after",
    ]


def _empty_edges(threshold: float) -> pd.DataFrame:
    df = pd.DataFrame(columns=_edge_columns())
    df["threshold"] = df.get("threshold", pd.Series(dtype=float))
    return df


def estimate_cycles_from_edges(edges: pd.DataFrame, edge_type: str = "rising") -> pd.DataFrame:
    """Estimate cycles from repeated command edges.

    A cycle is defined as the interval between consecutive edges of the selected
    type. For a binary command signal this usually means rising-to-rising cycles.
    """
    if edges is None or edges.empty:
        return pd.DataFrame(columns=_cycle_columns())

    edge_type = edge_type.lower().strip()
    g = edges[edges["edge_type"].str.lower() == edge_type].copy()
    g = g.sort_values("time_s").reset_index(drop=True)

    if len(g) < 2:
        return pd.DataFrame(columns=_cycle_columns())

    rows = []
    for i in range(len(g) - 1):
        start = g.iloc[i]
        end = g.iloc[i + 1]
        rows.append(
            {
                "cycle_index": i + 1,
                "start_time_s": float(start["time_s"]),
                "end_time_s": float(end["time_s"]),
                "duration_s": float(end["time_s"] - start["time_s"]),
                "start_sample_index": int(start["sample_index"]),
                "end_sample_index": int(end["sample_index"]),
            }
        )

    return pd.DataFrame(rows, columns=_cycle_columns())


def _cycle_columns() -> list[str]:
    return [
        "cycle_index",
        "start_time_s",
        "end_time_s",
        "duration_s",
        "start_sample_index",
        "end_sample_index",
    ]


def summarise_cycle_stability(cycles: pd.DataFrame) -> dict[str, float | int]:
    """Summarise cycle-duration stability."""
    if cycles is None or cycles.empty or "duration_s" not in cycles:
        return {
            "n_cycles": 0,
            "mean_duration_s": np.nan,
            "median_duration_s": np.nan,
            "std_duration_s": np.nan,
            "cv_duration_percent": np.nan,
            "min_duration_s": np.nan,
            "max_duration_s": np.nan,
            "max_abs_deviation_from_median_s": np.nan,
        }

    duration = as_1d_float_array(cycles["duration_s"])
    duration = duration[np.isfinite(duration)]
    if len(duration) == 0:
        return summarise_cycle_stability(pd.DataFrame())

    mean = float(np.mean(duration))
    median = float(np.median(duration))
    std = float(np.std(duration, ddof=0))

    return {
        "n_cycles": int(len(duration)),
        "mean_duration_s": mean,
        "median_duration_s": median,
        "std_duration_s": std,
        "cv_duration_percent": float(100.0 * std / mean) if mean != 0 else np.nan,
        "min_duration_s": float(np.min(duration)),
        "max_duration_s": float(np.max(duration)),
        "max_abs_deviation_from_median_s": float(np.max(np.abs(duration - median))),
    }


def match_response_delays(
    command_edges: pd.DataFrame,
    response_edges: pd.DataFrame,
    max_delay_s: float | None = None,
) -> pd.DataFrame:
    """Match each command edge to the first later response edge.

    The returned table includes unmatched command events. If ``max_delay_s`` is
    supplied, later responses outside the allowed window are treated as unmatched.
    """
    if command_edges is None or command_edges.empty:
        return pd.DataFrame(columns=_delay_columns())

    cmd = command_edges.sort_values("time_s").reset_index(drop=True)
    rsp = (
        response_edges.sort_values("time_s").reset_index(drop=True)
        if response_edges is not None and not response_edges.empty
        else pd.DataFrame(columns=_edge_columns())
    )

    max_delay = float(max_delay_s) if max_delay_s is not None else np.inf
    rows = []
    response_pointer = 0

    for i, command in cmd.iterrows():
        command_time = float(command["time_s"])

        while response_pointer < len(rsp) and float(rsp.loc[response_pointer, "time_s"]) < command_time:
            response_pointer += 1

        matched = False
        response_time = np.nan
        response_sample_index = np.nan
        delay_s = np.nan

        if response_pointer < len(rsp):
            candidate = rsp.loc[response_pointer]
            candidate_time = float(candidate["time_s"])
            candidate_delay = candidate_time - command_time

            if candidate_delay <= max_delay:
                matched = True
                response_time = candidate_time
                response_sample_index = int(candidate["sample_index"])
                delay_s = float(candidate_delay)
                response_pointer += 1

        rows.append(
            {
                "match_index": i + 1,
                "command_event_index": int(command["event_index"]),
                "command_sample_index": int(command["sample_index"]),
                "command_time_s": command_time,
                "response_sample_index": response_sample_index,
                "response_time_s": response_time,
                "delay_s": delay_s,
                "matched": bool(matched),
            }
        )

    return pd.DataFrame(rows, columns=_delay_columns())


def _delay_columns() -> list[str]:
    return [
        "match_index",
        "command_event_index",
        "command_sample_index",
        "command_time_s",
        "response_sample_index",
        "response_time_s",
        "delay_s",
        "matched",
    ]


def summarise_delay_drift(delays: pd.DataFrame) -> dict[str, float | int]:
    """Summarise response-delay statistics and simple linear drift."""
    if delays is None or delays.empty or "delay_s" not in delays:
        return {
            "n_matches": 0,
            "mean_delay_s": np.nan,
            "median_delay_s": np.nan,
            "std_delay_s": np.nan,
            "min_delay_s": np.nan,
            "max_delay_s": np.nan,
            "delay_drift_s_per_cycle": np.nan,
            "delay_drift_s_per_second": np.nan,
        }

    g = delays[delays["matched"]].copy() if "matched" in delays else delays.copy()
    g = g[np.isfinite(g["delay_s"])]

    if g.empty:
        return summarise_delay_drift(pd.DataFrame())

    delay = as_1d_float_array(g["delay_s"])
    x_cycle = np.arange(len(delay), dtype=float)
    x_time = as_1d_float_array(g["command_time_s"]) if "command_time_s" in g else x_cycle

    drift_cycle = _safe_polyfit_slope(x_cycle, delay)
    drift_time = _safe_polyfit_slope(x_time, delay)

    return {
        "n_matches": int(len(delay)),
        "mean_delay_s": float(np.mean(delay)),
        "median_delay_s": float(np.median(delay)),
        "std_delay_s": float(np.std(delay, ddof=0)),
        "min_delay_s": float(np.min(delay)),
        "max_delay_s": float(np.max(delay)),
        "delay_drift_s_per_cycle": drift_cycle,
        "delay_drift_s_per_second": drift_time,
    }


def _safe_polyfit_slope(x: np.ndarray, y: np.ndarray) -> float:
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if len(x) < 2 or np.isclose(np.max(x), np.min(x)):
        return np.nan
    return float(np.polyfit(x, y, 1)[0])


def estimate_active_window(
    time_s: Iterable[float],
    values: Iterable[float],
    rel_threshold: float = 0.02,
    min_abs_threshold: float = 1e-9,
) -> dict[str, float | int | str]:
    """Estimate the active time window of one signal.

    This is a review aid. It mirrors the generic activity-trim logic used by the
    metadata-first workflow and does not assume that zero is invalid.
    """
    t = as_1d_float_array(time_s)
    y = as_1d_float_array(values)
    if len(t) != len(y):
        raise ValueError("time_s and values must have the same length")

    if len(y) == 0:
        return _empty_active_window("empty")

    finite_mask = np.isfinite(t) & np.isfinite(y)
    if not finite_mask.any():
        return _empty_active_window("all invalid")

    finite_y = y[finite_mask]
    rng = float(np.nanmax(finite_y) - np.nanmin(finite_y))
    if rng <= 1e-12:
        return {
            "first_active_index": 0,
            "last_active_index": len(y) - 1,
            "first_active_time_s": float(t[0]),
            "last_active_time_s": float(t[-1]),
            "active_duration_s": float(t[-1] - t[0]) if len(t) > 1 else 0.0,
            "activity_status": "constant",
        }

    baseline_window = max(5, min(len(y), int(0.02 * len(y))))
    baseline = float(np.nanmedian(y[:baseline_window]))
    threshold = max(float(min_abs_threshold), float(rel_threshold) * rng)
    active = finite_mask & (np.abs(y - baseline) > threshold)

    if not active.any():
        return {
            "first_active_index": 0,
            "last_active_index": len(y) - 1,
            "first_active_time_s": float(t[0]),
            "last_active_time_s": float(t[-1]),
            "active_duration_s": float(t[-1] - t[0]) if len(t) > 1 else 0.0,
            "activity_status": "no clear activity transition",
        }

    idx = np.where(active)[0]
    first = int(idx[0])
    last = int(idx[-1])
    return {
        "first_active_index": first,
        "last_active_index": last,
        "first_active_time_s": float(t[first]),
        "last_active_time_s": float(t[last]),
        "active_duration_s": float(t[last] - t[first]),
        "activity_status": "activity detected",
    }


def _empty_active_window(status: str) -> dict[str, float | int | str]:
    return {
        "first_active_index": np.nan,
        "last_active_index": np.nan,
        "first_active_time_s": np.nan,
        "last_active_time_s": np.nan,
        "active_duration_s": np.nan,
        "activity_status": status,
    }


def estimate_common_active_window(windows: pd.DataFrame) -> dict[str, float | str]:
    """Estimate a common active time range from per-channel active windows."""
    if windows is None or windows.empty:
        return {
            "common_active_start_s": np.nan,
            "common_active_end_s": np.nan,
            "common_active_duration_s": np.nan,
            "common_active_status": "no windows",
        }

    starts = pd.to_numeric(windows["first_active_time_s"], errors="coerce")
    ends = pd.to_numeric(windows["last_active_time_s"], errors="coerce")

    if starts.notna().sum() == 0 or ends.notna().sum() == 0:
        return {
            "common_active_start_s": np.nan,
            "common_active_end_s": np.nan,
            "common_active_duration_s": np.nan,
            "common_active_status": "no valid windows",
        }

    common_start = float(starts.max())
    common_end = float(ends.min())
    duration = common_end - common_start

    return {
        "common_active_start_s": common_start,
        "common_active_end_s": common_end,
        "common_active_duration_s": duration,
        "common_active_status": "overlap" if duration >= 0 else "no overlap",
    }


def build_diagnostic_summary(
    command_edges: pd.DataFrame,
    response_edges: pd.DataFrame,
    cycles: pd.DataFrame,
    delays: pd.DataFrame,
) -> DiagnosticSummary:
    """Build a compact summary object from diagnostic tables."""
    cycle_summary = summarise_cycle_stability(cycles)
    delay_summary = summarise_delay_drift(delays)

    return DiagnosticSummary(
        n_command_edges=len(command_edges) if command_edges is not None else 0,
        n_response_edges=len(response_edges) if response_edges is not None else 0,
        n_cycles=int(cycle_summary["n_cycles"]),
        n_matched_delays=int(delay_summary["n_matches"]),
        median_cycle_duration_s=float(cycle_summary["median_duration_s"]),
        median_response_delay_s=float(delay_summary["median_delay_s"]),
        delay_drift_s_per_cycle=float(delay_summary["delay_drift_s_per_cycle"]),
    )


def write_diagnostic_outputs(
    output_dir: Path,
    command_edges: pd.DataFrame,
    response_edges: pd.DataFrame,
    cycles: pd.DataFrame,
    delays: pd.DataFrame,
) -> Path:
    """Write diagnostic CSV files and a plain-text summary."""
    output_dir = Path(output_dir)
    csv_dir = output_dir / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    command_edges.to_csv(csv_dir / "command_edges.csv", index=False)
    response_edges.to_csv(csv_dir / "response_edges.csv", index=False)
    cycles.to_csv(csv_dir / "cycle_duration_stability.csv", index=False)
    delays.to_csv(csv_dir / "response_delays.csv", index=False)

    summary = build_diagnostic_summary(command_edges, response_edges, cycles, delays)
    summary_path = output_dir / "engineering_diagnostic_summary.txt"
    summary_path.write_text(summary.to_text(), encoding="utf-8")
    return summary_path
