# -*- coding: utf-8 -*-
"""
Optional TDMS Plot Maker
========================

Use this only AFTER the main no-plot checker has worked.

It reads the CSV created by the main checker and creates only a few
small downsampled plots for the most active channels.

Edit OUTPUT_FOLDER below to the folder created by the main checker.
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from nptdms import TdmsFile


OUTPUT_FOLDER = Path(r"C:\Your\Folder\Here\tdms_general_sync_outputs")

MAX_GROUPS_TO_PLOT = 1
MAX_CHANNELS_PER_GROUP = 2
MAX_POINTS = 3000


def normalise_tdms_name(name):
    return str(name).split("\n")[0].strip()


def get_channel_start_time(channel):
    start = channel.properties.get("wf_start_time", None)
    try:
        return pd.to_datetime(start)
    except Exception:
        return pd.NaT


def get_channel_dt(channel):
    try:
        return float(channel.properties.get("wf_increment", np.nan))
    except Exception:
        return np.nan


def read_channel_downsampled(channel, max_points=3000):
    y = np.asarray(channel[:], dtype=float)
    n = len(y)

    if n > max_points:
        step = int(np.ceil(n / max_points))
        idx = np.arange(0, n, step)
        y = y[idx]
    else:
        idx = np.arange(n)

    dt = get_channel_dt(channel)
    start = get_channel_start_time(channel)

    if np.isfinite(dt) and dt > 0:
        t = idx * dt
    else:
        t = idx.astype(float)

    if pd.isna(start):
        real_time = None
    else:
        real_time = start + pd.to_timedelta(t, unit="s")

    return t, real_time, y


def choose_channels(metadata):
    first_file = metadata["file"].iloc[0]
    meta0 = metadata[metadata["file"] == first_file].copy()

    group_priority = (
        meta0.groupby("group")["is_changing"]
        .sum()
        .sort_values(ascending=False)
    )

    selected = {}

    for group in group_priority.head(MAX_GROUPS_TO_PLOT).index:
        g = meta0[meta0["group"] == group].copy()
        g = g.sort_values(
            ["is_changing", "range_value", "std_value"],
            ascending=[False, False, False]
        )
        selected[group] = g["channel"].head(MAX_CHANNELS_PER_GROUP).tolist()

    return Path(first_file), selected


def plot_selected_group(path, group_name, channel_names, output_folder, use_real_time=False):
    tdms = TdmsFile.read(path)

    data = {}

    for group in tdms.groups():
        if group.name != group_name:
            continue

        for channel in group.channels():
            ch_name = normalise_tdms_name(channel.name)

            if ch_name in channel_names:
                t, real_time, y = read_channel_downsampled(channel, max_points=MAX_POINTS)
                data[ch_name] = (t, real_time, y)

    if not data:
        return

    n = len(data)
    fig, axes = plt.subplots(n, 1, figsize=(14, max(4, 3 * n)), sharex=True)

    if n == 1:
        axes = [axes]

    for ax, (ch_name, (t, real_time, y)) in zip(axes, data.items()):
        x = real_time if use_real_time and real_time is not None else t
        ax.plot(x, y, linewidth=0.8)
        ax.set_title(ch_name)
        ax.set_ylabel("value")
        ax.grid(True, alpha=0.3)

    if use_real_time:
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        fig.autofmt_xdate()
        suffix = "real_time"
        xlabel = "real time"
    else:
        suffix = "test_time"
        xlabel = "test time [s]"

    axes[-1].set_xlabel(xlabel)

    fig.suptitle(f"{path.name} | {group_name}")
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    safe_group = re.sub(r"[^A-Za-z0-9_]+", "_", group_name)
    out_dir = output_folder / "optional_plots"
    out_dir.mkdir(exist_ok=True)

    out = out_dir / f"{path.stem}_{safe_group}_{suffix}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print("Saved:", out)


def main():
    metadata_path = OUTPUT_FOLDER / "csv" / "channel_metadata_all_channels.csv"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Cannot find: {metadata_path}")

    metadata = pd.read_csv(metadata_path)
    path, selected = choose_channels(metadata)

    print("File:", path)
    print("Selected channels:")
    for group, channels in selected.items():
        print(" ", group, channels)
        plot_selected_group(path, group, channels, OUTPUT_FOLDER, use_real_time=False)
        plot_selected_group(path, group, channels, OUTPUT_FOLDER, use_real_time=True)


if __name__ == "__main__":
    main()
