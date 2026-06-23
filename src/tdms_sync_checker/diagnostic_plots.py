"""Optional plotting helpers for engineering diagnostics."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _get_pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - depends on optional dependency
        raise ImportError(
            "matplotlib is required for diagnostic plots. Install with `pip install -e \".[plot]\"` "
            "or `pip install -e \".[dev]\"`."
        ) from exc
    return plt


def plot_cycle_duration(cycles: pd.DataFrame, output_path: Path) -> Path:
    """Plot cycle duration against cycle index."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt = _get_pyplot()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if cycles is not None and not cycles.empty:
        ax.plot(cycles["cycle_index"], cycles["duration_s"], marker="o", linewidth=1)

    ax.set_xlabel("Cycle index")
    ax.set_ylabel("Duration [s]")
    ax.set_title("Cycle duration stability")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_response_delay(delays: pd.DataFrame, output_path: Path) -> Path:
    """Plot response delay against command-event index."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt = _get_pyplot()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if delays is not None and not delays.empty:
        g = delays[delays["matched"]].copy() if "matched" in delays else delays.copy()
        if not g.empty:
            ax.plot(g["match_index"], g["delay_s"], marker="o", linewidth=1)

    ax.set_xlabel("Command event index")
    ax.set_ylabel("Delay [s]")
    ax.set_title("Command-response delay")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_command_response_overlay(
    time_s,
    command_values,
    response_values,
    output_path: Path,
    max_points: int = 10_000,
) -> Path:
    """Plot a downsampled command/response overlay for visual review."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    t = np.asarray(time_s, dtype=float)
    cmd = np.asarray(command_values, dtype=float)
    rsp = np.asarray(response_values, dtype=float)

    n = min(len(t), len(cmd), len(rsp))
    t = t[:n]
    cmd = cmd[:n]
    rsp = rsp[:n]

    if n > max_points:
        step = int(np.ceil(n / max_points))
        t = t[::step]
        cmd = cmd[::step]
        rsp = rsp[::step]

    plt = _get_pyplot()
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.plot(t, cmd, linewidth=1, label="Command")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Command")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(t, rsp, linewidth=1, label="Response", linestyle="--")
    ax2.set_ylabel("Response")

    ax1.set_title("Command/response overlay")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path
