"""Run optional engineering diagnostics on selected TDMS channels.

Example
-------
python scripts/run_engineering_diagnostics.py ^
    --input examples/data/synthetic_tdms_reference.tdms ^
    --output examples/output_engineering_diagnostics ^
    --command-channel FD_Command ^
    --response-channel Inverter_Power ^
    --command-direction rising ^
    --response-direction rising ^
    --max-delay-s 2.0 ^
    --make-plots
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from nptdms import TdmsFile

from tdms_sync_checker.core import get_channel_dt, normalise_tdms_name
from tdms_sync_checker.diagnostics import (
    build_time_axis,
    detect_edges,
    estimate_cycles_from_edges,
    match_response_delays,
    write_diagnostic_outputs,
)
from tdms_sync_checker.diagnostic_plots import plot_cycle_duration, plot_response_delay


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optional command/response engineering diagnostics for selected TDMS channels."
    )
    parser.add_argument("--input", required=True, help="Input TDMS file")
    parser.add_argument("--output", required=True, help="Output folder")
    parser.add_argument("--command-channel", required=True, help="Command channel name or case-insensitive substring")
    parser.add_argument("--response-channel", required=True, help="Response channel name or case-insensitive substring")
    parser.add_argument("--command-group", default=None, help="Optional command group name or substring")
    parser.add_argument("--response-group", default=None, help="Optional response group name or substring")
    parser.add_argument("--command-threshold", type=float, default=None, help="Optional command threshold")
    parser.add_argument("--response-threshold", type=float, default=None, help="Optional response threshold")
    parser.add_argument(
        "--command-direction",
        choices=["rising", "falling", "both"],
        default="rising",
        help="Command edge direction",
    )
    parser.add_argument(
        "--response-direction",
        choices=["rising", "falling", "both"],
        default="rising",
        help="Response edge direction",
    )
    parser.add_argument(
        "--min-cycle-interval-s",
        type=float,
        default=0.0,
        help="Minimum accepted time between command edges",
    )
    parser.add_argument(
        "--max-delay-s",
        type=float,
        default=None,
        help="Maximum allowed command-response delay for matching",
    )
    parser.add_argument("--make-plots", action="store_true", help="Create optional PNG diagnostic plots")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    tdms = TdmsFile.read(input_path)

    command_group, command_channel = find_channel(tdms, args.command_channel, args.command_group)
    response_group, response_channel = find_channel(tdms, args.response_channel, args.response_group)

    command_values = np.asarray(command_channel[:], dtype=float)
    response_values = np.asarray(response_channel[:], dtype=float)

    command_dt = get_channel_dt(command_channel)
    response_dt = get_channel_dt(response_channel)

    command_time = build_time_axis(len(command_values), dt_s=command_dt)
    response_time = build_time_axis(len(response_values), dt_s=response_dt)

    command_edges = detect_edges(
        command_time,
        command_values,
        threshold=args.command_threshold,
        direction=args.command_direction,
        min_interval_s=args.min_cycle_interval_s,
    )
    response_edges = detect_edges(
        response_time,
        response_values,
        threshold=args.response_threshold,
        direction=args.response_direction,
    )
    cycle_edge_type = args.command_direction if args.command_direction != "both" else "rising"
    cycles = estimate_cycles_from_edges(command_edges, edge_type=cycle_edge_type)
    delays = match_response_delays(command_edges, response_edges, max_delay_s=args.max_delay_s)

    metadata = pd.DataFrame(
        [
            {
                "role": "command",
                "group": command_group.name,
                "channel": normalise_tdms_name(command_channel.name),
                "samples": len(command_values),
                "dt_s": command_dt,
            },
            {
                "role": "response",
                "group": response_group.name,
                "channel": normalise_tdms_name(response_channel.name),
                "samples": len(response_values),
                "dt_s": response_dt,
            },
        ]
    )
    metadata.to_csv(output_dir / "selected_channels.csv", index=False)

    summary_path = write_diagnostic_outputs(output_dir, command_edges, response_edges, cycles, delays)

    if args.make_plots:
        plot_dir = output_dir / "figures"
        plot_cycle_duration(cycles, plot_dir / "cycle_duration_stability.png")
        plot_response_delay(delays, plot_dir / "response_delay.png")

    print("Engineering diagnostics complete.")
    print(f"Input file: {input_path}")
    print(f"Command: {command_group.name} / {normalise_tdms_name(command_channel.name)}")
    print(f"Response: {response_group.name} / {normalise_tdms_name(response_channel.name)}")
    print(f"Output folder: {output_dir}")
    print(f"Summary: {summary_path}")


def find_channel(tdms: TdmsFile, channel_query: str, group_query: str | None = None):
    """Find a TDMS channel by exact normalised name or case-insensitive substring."""
    channel_query_norm = channel_query.lower().strip()
    group_query_norm = group_query.lower().strip() if group_query else None

    candidates = []
    for group in tdms.groups():
        group_name_norm = group.name.lower().strip()
        if group_query_norm and group_query_norm not in group_name_norm:
            continue

        for channel in group.channels():
            channel_name = normalise_tdms_name(channel.name)
            channel_name_norm = channel_name.lower().strip()
            candidates.append((group, channel, channel_name))

            if channel_name_norm == channel_query_norm:
                return group, channel

    substring_matches = [
        (group, channel, name) for group, channel, name in candidates if channel_query_norm in name.lower()
    ]

    if len(substring_matches) == 1:
        group, channel, _ = substring_matches[0]
        return group, channel

    available = "\n".join(f"- {group.name} / {name}" for group, _, name in candidates[:80])
    if len(substring_matches) > 1:
        matches = "\n".join(f"- {group.name} / {name}" for group, _, name in substring_matches[:30])
        raise ValueError(
            "Channel query matched more than one channel. "
            "Use --command-group/--response-group or a more specific name.\n"
            f"Matches:\n{matches}"
        )

    raise ValueError(
        f"Could not find channel matching {channel_query!r}.\n"
        f"Available channels include:\n{available}"
    )


if __name__ == "__main__":
    main()
