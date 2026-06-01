from __future__ import annotations

from pathlib import Path
import re
import numpy as np
import pandas as pd
from nptdms import TdmsFile


ACTIVITY_REL_THRESHOLD = 0.02
ACTIVITY_MIN_ABS_THRESHOLD = 1e-9
MOSTLY_ZERO_PERCENT = 95.0


def normalise_tdms_name(name):
    return str(name).split("\n")[0].strip()


def safe_float(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default


def get_channel_start_time(channel):
    start = channel.properties.get("wf_start_time", None)
    if start is None:
        return pd.NaT
    try:
        return pd.to_datetime(start)
    except Exception:
        return pd.NaT


def get_channel_dt(channel):
    return safe_float(channel.properties.get("wf_increment", np.nan))


def value_stats(values):
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    n = len(values)

    if len(finite) == 0:
        return {
            "min_value": np.nan,
            "max_value": np.nan,
            "mean_value": np.nan,
            "std_value": np.nan,
            "range_value": np.nan,
            "n_nan": n,
            "n_zero": 0,
            "zero_percent": np.nan,
            "is_constant": True,
            "is_changing": False,
        }

    n_zero = int(np.sum(np.abs(finite) <= 1e-12))
    zero_percent = 100.0 * n_zero / len(finite)

    std = float(np.nanstd(finite))
    minv = float(np.nanmin(finite))
    maxv = float(np.nanmax(finite))
    rng = maxv - minv

    return {
        "min_value": minv,
        "max_value": maxv,
        "mean_value": float(np.nanmean(finite)),
        "std_value": std,
        "range_value": rng,
        "n_nan": int(np.isnan(values).sum()),
        "n_zero": n_zero,
        "zero_percent": zero_percent,
        "is_constant": bool(std <= 1e-12 or rng <= 1e-12),
        "is_changing": bool(std > 1e-12 and rng > 1e-12),
    }


def suggested_activity_trim(values):
    """Estimate possible start/end buffer region from signal activity.

    This is a generic suggestion only. It does not assume zero is invalid.
    Zero may be a valid operating state in TDMS channels.
    """
    y = np.asarray(values, dtype=float)
    n = len(y)

    if n == 0:
        return {
            "suggested_first_active_index": np.nan,
            "suggested_last_active_index": np.nan,
            "suggested_samples_removed_start": 0,
            "suggested_samples_removed_end": 0,
            "suggested_samples_kept": 0,
            "suggested_samples_removed_total": 0,
            "activity_status": "empty",
        }

    finite_mask = np.isfinite(y)

    if not finite_mask.any():
        return {
            "suggested_first_active_index": np.nan,
            "suggested_last_active_index": np.nan,
            "suggested_samples_removed_start": n,
            "suggested_samples_removed_end": 0,
            "suggested_samples_kept": 0,
            "suggested_samples_removed_total": n,
            "activity_status": "all invalid",
        }

    finite_y = y[finite_mask]
    rng = float(np.nanmax(finite_y) - np.nanmin(finite_y))

    if rng <= 1e-12:
        return {
            "suggested_first_active_index": 0,
            "suggested_last_active_index": n - 1,
            "suggested_samples_removed_start": 0,
            "suggested_samples_removed_end": 0,
            "suggested_samples_kept": n,
            "suggested_samples_removed_total": 0,
            "activity_status": "constant",
        }

    baseline_window = max(5, min(n, int(0.02 * n)))
    baseline = float(np.nanmedian(y[:baseline_window]))
    threshold = max(ACTIVITY_MIN_ABS_THRESHOLD, ACTIVITY_REL_THRESHOLD * rng)

    active = finite_mask & (np.abs(y - baseline) > threshold)

    if not active.any():
        return {
            "suggested_first_active_index": 0,
            "suggested_last_active_index": n - 1,
            "suggested_samples_removed_start": 0,
            "suggested_samples_removed_end": 0,
            "suggested_samples_kept": n,
            "suggested_samples_removed_total": 0,
            "activity_status": "no clear activity transition",
        }

    idx = np.where(active)[0]
    first = int(idx[0])
    last = int(idx[-1])

    return {
        "suggested_first_active_index": first,
        "suggested_last_active_index": last,
        "suggested_samples_removed_start": first,
        "suggested_samples_removed_end": n - 1 - last,
        "suggested_samples_kept": last - first + 1,
        "suggested_samples_removed_total": first + (n - 1 - last),
        "activity_status": "activity detected",
    }


def scan_tdms_file(path: Path, log_func=print):
    """Scan one TDMS file. Each channel is read once."""
    tdms = TdmsFile.read(path)
    rows = []
    trim_rows = []

    groups = tdms.groups()

    for gi, group in enumerate(groups, start=1):
        log_func(f"  Group {gi}/{len(groups)}: {group.name}")

        for channel in group.channels():
            ch_name = normalise_tdms_name(channel.name)
            values = np.asarray(channel[:], dtype=float)
            n = len(values)

            dt = get_channel_dt(channel)
            start = get_channel_start_time(channel)

            stats = value_stats(values)
            trim = suggested_activity_trim(values)

            rows.append({
                "file": str(path),
                "file_name": path.name,
                "group": group.name,
                "channel": ch_name,
                "reported_start_time": start,
                "reported_dt_s": dt,
                "reported_sample_rate_hz": 1.0 / dt if np.isfinite(dt) and dt > 0 else np.nan,
                "raw_samples": n,
                "raw_duration_s": (n - 1) * dt if n > 0 and np.isfinite(dt) else np.nan,
                **stats,
                "mostly_zero": bool(stats["zero_percent"] >= MOSTLY_ZERO_PERCENT) if np.isfinite(stats["zero_percent"]) else False,
            })

            trim_rows.append({
                "file": str(path),
                "file_name": path.name,
                "group": group.name,
                "channel": ch_name,
                "raw_samples": n,
                **trim,
            })

    return pd.DataFrame(rows), pd.DataFrame(trim_rows)


def inside_group_sync(channel_scan: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (file, group), g in channel_scan.groupby(["file", "group"], dropna=False):
        starts = pd.to_datetime(g["reported_start_time"], errors="coerce")

        rows.append({
            "file": file,
            "file_name": g["file_name"].iloc[0],
            "group": group,
            "n_channels": len(g),
            "same_start_time": g["reported_start_time"].nunique(dropna=True) <= 1,
            "same_dt": g["reported_dt_s"].round(12).nunique(dropna=True) <= 1,
            "same_samples": g["raw_samples"].nunique(dropna=True) <= 1,
            "n_constant_channels": int(g["is_constant"].sum()),
            "n_changing_channels": int(g["is_changing"].sum()),
            "n_mostly_zero_channels": int(g["mostly_zero"].sum()),
            "min_start_time": starts.min(),
            "max_start_time": starts.max(),
            "max_start_diff_s": (starts.max() - starts.min()).total_seconds() if starts.notna().any() else np.nan,
            "min_dt_s": g["reported_dt_s"].min(),
            "max_dt_s": g["reported_dt_s"].max(),
            "min_samples": g["raw_samples"].min(),
            "max_samples": g["raw_samples"].max(),
        })

    return pd.DataFrame(rows)


def between_group_sync(channel_scan: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (file, group), g in channel_scan.groupby(["file", "group"], dropna=False):
        starts = pd.to_datetime(g["reported_start_time"], errors="coerce")
        start = starts.min()

        dt_mode = g["reported_dt_s"].mode(dropna=True)
        dt = dt_mode.iloc[0] if len(dt_mode) else np.nan

        duration_max = g["raw_duration_s"].max()

        rows.append({
            "file": file,
            "file_name": g["file_name"].iloc[0],
            "group": group,
            "n_channels": len(g),
            "group_start_time": start,
            "group_dt_s_mode": dt,
            "group_sample_rate_hz": 1.0 / dt if np.isfinite(dt) and dt > 0 else np.nan,
            "group_duration_s_max": duration_max,
            "n_changing_channels": int(g["is_changing"].sum()),
            "n_constant_channels": int(g["is_constant"].sum()),
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        starts = pd.to_datetime(df["group_start_time"], errors="coerce")
        earliest = starts.min()

        df["offset_from_earliest_group_s"] = (starts - earliest).dt.total_seconds()
        df["group_end_time"] = starts + pd.to_timedelta(df["group_duration_s_max"], unit="s")

        latest_start = starts.max()
        earliest_end = pd.to_datetime(df["group_end_time"], errors="coerce").min()

        df["common_overlap_start"] = latest_start
        df["common_overlap_end"] = earliest_end
        df["common_overlap_duration_s"] = (
            (earliest_end - latest_start).total_seconds()
            if pd.notna(latest_start) and pd.notna(earliest_end)
            else np.nan
        )

    return df


def infer_test_id(path: Path) -> str:
    return re.sub(r"[_-]\d{3,}$", "", path.stem)


def split_file_continuity(paths: list[Path], channel_scan: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for path in paths:
        scan = channel_scan[channel_scan["file"] == str(path)].copy()

        starts = pd.to_datetime(scan["reported_start_time"], errors="coerce")
        start = starts.min()
        end = (starts + pd.to_timedelta(scan["raw_duration_s"], unit="s")).max()

        rows.append({
            "test_id": infer_test_id(path),
            "file": str(path),
            "file_name": path.name,
            "start_time": start,
            "end_time": end,
            "n_groups": scan["group"].nunique(),
            "n_channels": len(scan),
        })

    df = pd.DataFrame(rows).sort_values(["test_id", "start_time", "file"])

    out = []

    for test_id, g in df.groupby("test_id", dropna=False):
        prev_end = None

        for i, row in g.reset_index(drop=True).iterrows():
            if prev_end is None or pd.isna(prev_end) or pd.isna(row["start_time"]):
                gap = np.nan
            else:
                gap = (row["start_time"] - prev_end).total_seconds()

            if i == 0:
                status = "first section"
            elif gap < 0:
                status = "overlap"
            elif gap > 0.5:
                status = "gap"
            else:
                status = "continuous"

            new_row = row.to_dict()
            new_row["section_number"] = i + 1
            new_row["gap_from_previous_s"] = gap
            new_row["section_status"] = status

            out.append(new_row)
            prev_end = row["end_time"]

    return pd.DataFrame(out)


def build_summary_text(result: dict) -> str:
    channel_scan = result["channel_scan"]
    inside = result["inside_group"]
    between = result["between_group"]
    split = result["split_file"]
    trim = result["suggested_trim"]

    n_files = channel_scan["file"].nunique() if not channel_scan.empty else 0
    n_file_groups = channel_scan[["file", "group"]].drop_duplicates().shape[0] if not channel_scan.empty else 0
    n_unique_groups = channel_scan["group"].nunique() if not channel_scan.empty else 0
    n_channels = len(channel_scan)

    n_changing = int(channel_scan["is_changing"].sum()) if "is_changing" in channel_scan else 0
    n_constant = int(channel_scan["is_constant"].sum()) if "is_constant" in channel_scan else 0
    n_mostly_zero = int(channel_scan["mostly_zero"].sum()) if "mostly_zero" in channel_scan else 0

    if not between.empty and "offset_from_earliest_group_s" in between.columns:
        max_group_start_diff = between["offset_from_earliest_group_s"].max()
    else:
        max_group_start_diff = np.nan

    if not between.empty and "common_overlap_duration_s" in between.columns:
        min_overlap = between["common_overlap_duration_s"].min()
    else:
        min_overlap = np.nan

    if not inside.empty:
        groups_with_dt_mismatch = int((~inside["same_dt"]).sum())
        groups_with_sample_mismatch = int((~inside["same_samples"]).sum())
        groups_with_start_mismatch = int((~inside["same_start_time"]).sum())
    else:
        groups_with_dt_mismatch = 0
        groups_with_sample_mismatch = 0
        groups_with_start_mismatch = 0

    if not split.empty:
        n_gaps = int((split["section_status"] == "gap").sum())
        n_overlaps = int((split["section_status"] == "overlap").sum())
    else:
        n_gaps = 0
        n_overlaps = 0

    if trim is not None and not trim.empty and "suggested_samples_removed_total" in trim.columns:
        trim_nonzero = int((trim["suggested_samples_removed_total"].fillna(0) > 0).sum())
        max_trim = trim["suggested_samples_removed_total"].max()
    else:
        trim_nonzero = 0
        max_trim = np.nan

    top_groups = []
    if not channel_scan.empty:
        group_summary = (
            channel_scan
            .groupby("group")
            .agg(
                channels=("channel", "count"),
                changing=("is_changing", "sum"),
                constant=("is_constant", "sum"),
                mostly_zero=("mostly_zero", "sum"),
            )
            .sort_values(["changing", "channels"], ascending=False)
            .head(10)
        )
        for group, row in group_summary.iterrows():
            top_groups.append(
                f"  {group}: {int(row['channels'])} channels, "
                f"{int(row['changing'])} changing, "
                f"{int(row['constant'])} constant, "
                f"{int(row['mostly_zero'])} mostly-zero"
            )

    lines = []
    lines.append("SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Files analysed: {n_files}")
    lines.append(f"Unique group names: {n_unique_groups}")
    lines.append(f"File/group combinations: {n_file_groups}")
    lines.append(f"Total file/channel rows found: {n_channels}")
    lines.append("")
    lines.append("Channel activity:")
    lines.append(f"  Changing channels: {n_changing}")
    lines.append(f"  Constant channels: {n_constant}")
    lines.append(f"  Mostly-zero channels: {n_mostly_zero}")
    lines.append("")
    lines.append("Timing consistency:")
    lines.append(f"  Max reported group start-time offset: {max_group_start_diff:.3f} s" if np.isfinite(max_group_start_diff) else "  Max reported group start-time offset: n/a")
    lines.append(f"  Minimum common overlap duration: {min_overlap:.3f} s" if np.isfinite(min_overlap) else "  Minimum common overlap duration: n/a")
    lines.append(f"  File/groups with dt mismatch inside group: {groups_with_dt_mismatch}")
    lines.append(f"  File/groups with sample-count mismatch inside group: {groups_with_sample_mismatch}")
    lines.append(f"  File/groups with start-time mismatch inside group: {groups_with_start_mismatch}")
    lines.append("")
    lines.append("Split-file continuity:")
    lines.append(f"  Gaps detected: {n_gaps}")
    lines.append(f"  Overlaps detected: {n_overlaps}")
    lines.append("")
    lines.append("Suggested activity trim:")
    lines.append(f"  Channels with suggested trim > 0 samples: {trim_nonzero}")
    lines.append(f"  Maximum suggested samples removed in one channel: {max_trim:.0f}" if np.isfinite(max_trim) else "  Maximum suggested samples removed in one channel: n/a")
    lines.append("")
    lines.append("Top groups by changing channels:")
    lines.extend(top_groups if top_groups else ["  n/a"])
    lines.append("")
    lines.append("Interpretation:")
    if groups_with_dt_mismatch or groups_with_sample_mismatch or groups_with_start_mismatch:
        lines.append("  Some file/groups have internal timing differences. Review inside_group_sync.csv.")
    else:
        lines.append("  No inside-group timing mismatch was detected from metadata.")

    if np.isfinite(max_group_start_diff) and max_group_start_diff > 1:
        lines.append("  Groups do not all start at the same reported time. Review between_group_sync.csv.")
    else:
        lines.append("  Group start times look close from metadata.")

    if n_gaps or n_overlaps:
        lines.append("  Split-file continuity has gaps or overlaps. Review split_file_continuity.csv.")
    else:
        lines.append("  No split-file gaps/overlaps detected with the current threshold.")

    lines.append("")
    lines.append("Outputs written to:")
    lines.append(f"  {result['output_dir']}")

    return "\n".join(lines)



def build_report_preview_text(result: dict, summary_text: str, max_rows: int = 25) -> str:
    """Build a GUI-friendly plain-text preview of the HTML report.

    Tkinter does not include a native HTML renderer. The full HTML report is still
    written to disk and can be opened in a browser. This text preview mirrors the
    report structure inside the GUI without adding heavy dependencies.
    """
    sections = [
        ("EXECUTIVE SUMMARY", summary_text),
        ("INSIDE-GROUP SYNCHRONISATION", result["inside_group"]),
        ("BETWEEN-GROUP SYNCHRONISATION", result["between_group"]),
        ("SPLIT-FILE CONTINUITY", result["split_file"]),
        ("SUGGESTED ACTIVITY TRIM", result["suggested_trim"]),
        ("ALL CHANNELS FOUND", result["channel_scan"]),
    ]

    lines = []
    lines.append("GENERAL TDMS SYNCHRONISATION REPORT")
    lines.append("=" * 90)
    lines.append("This is a GUI preview of the report.")
    lines.append("The full formatted HTML report is saved separately and can be opened in a browser.")
    lines.append("")

    for title, content in sections:
        lines.append("")
        lines.append(title)
        lines.append("-" * len(title))

        if isinstance(content, pd.DataFrame):
            if content.empty:
                lines.append("No data.")
            else:
                n_rows = len(content)
                preview = content.head(max_rows).copy()
                lines.append(f"Showing first {min(max_rows, n_rows)} rows of {n_rows}.")
                lines.append("")
                with pd.option_context(
                    "display.max_columns", None,
                    "display.width", 220,
                    "display.max_colwidth", 60,
                ):
                    lines.append(preview.to_string(index=False))
        else:
            lines.append(str(content))

        lines.append("")

    return "\n".join(lines)


def dataframe_to_html(df, max_rows=1000):
    if df is None or df.empty:
        return "<p>No data.</p>"

    if len(df) > max_rows:
        preview = df.head(max_rows).copy()
        note = f"<p><b>Note:</b> showing first {max_rows} rows of {len(df)}. Full table is in CSV/Excel.</p>"
        return note + preview.to_html(index=False, escape=False)

    return df.to_html(index=False, escape=False)


def write_excel_report(result: dict, output_dir: Path) -> Path:
    path = output_dir / "summary.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        result["channel_scan"].to_excel(writer, sheet_name="All channels", index=False)
        result["inside_group"].to_excel(writer, sheet_name="Inside groups", index=False)
        result["between_group"].to_excel(writer, sheet_name="Between groups", index=False)
        result["split_file"].to_excel(writer, sheet_name="Split files", index=False)
        result["suggested_trim"].to_excel(writer, sheet_name="Suggested trim", index=False)

    return path


def write_html_report(result: dict, output_dir: Path, summary_text: str) -> Path:
    html_path = output_dir / "report.html"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>General TDMS Synchronisation Report</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 30px;
    color: #222;
}}
h1, h2 {{
    color: #16324f;
}}
pre {{
    background: #f7f7f7;
    border: 1px solid #ddd;
    padding: 12px;
    white-space: pre-wrap;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 24px;
    font-size: 12px;
}}
th, td {{
    border: 1px solid #ccc;
    padding: 6px;
    text-align: left;
}}
th {{
    background: #f2f5f8;
}}
</style>
</head>
<body>

<h1>General TDMS Synchronisation Report</h1>

<h2>Executive summary</h2>
<pre>{summary_text}</pre>

<h2>Inside-group synchronisation</h2>
{dataframe_to_html(result["inside_group"])}

<h2>Between-group synchronisation</h2>
{dataframe_to_html(result["between_group"])}

<h2>Split-file continuity</h2>
{dataframe_to_html(result["split_file"])}

<h2>Suggested activity trim</h2>
<p>
This is a generic suggestion only. It identifies possible start/end buffer regions based on signal activity.
It does not assume that zeros are always bad.
</p>
{dataframe_to_html(result["suggested_trim"])}

<h2>All channels found</h2>
{dataframe_to_html(result["channel_scan"])}

</body>
</html>
"""

    html_path.write_text(html, encoding="utf-8")
    return html_path


def run_analysis(input_path: Path, output_dir: Path, log_func=print):
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "csv").mkdir(exist_ok=True)

    if input_path.is_dir():
        tdms_paths = sorted(input_path.glob("*.tdms"))
    else:
        tdms_paths = [input_path]

    if not tdms_paths:
        raise FileNotFoundError(f"No TDMS files found: {input_path}")

    log_func("")
    log_func("TDMS files to analyse:")
    for path in tdms_paths:
        log_func(f" - {path}")

    scans = []
    trims = []

    for i, path in enumerate(tdms_paths, start=1):
        log_func("")
        log_func(f"Scanning file {i}/{len(tdms_paths)}: {path.name}")
        scan_df, trim_df = scan_tdms_file(path, log_func=log_func)
        scans.append(scan_df)
        trims.append(trim_df)

    channel_scan = pd.concat(scans, ignore_index=True)
    suggested_trim = pd.concat(trims, ignore_index=True)

    channel_scan.to_csv(output_dir / "csv" / "channel_metadata_all_channels.csv", index=False)
    suggested_trim.to_csv(output_dir / "csv" / "suggested_activity_trim.csv", index=False)

    log_func("")
    log_func("Creating inside-group report...")
    inside = inside_group_sync(channel_scan)
    inside.to_csv(output_dir / "csv" / "inside_group_sync.csv", index=False)

    log_func("Creating between-group report...")
    between = between_group_sync(channel_scan)
    between.to_csv(output_dir / "csv" / "between_group_sync.csv", index=False)

    log_func("Checking split-file continuity...")
    split = split_file_continuity(tdms_paths, channel_scan)
    split.to_csv(output_dir / "csv" / "split_file_continuity.csv", index=False)

    result = {
        "paths": tdms_paths,
        "channel_scan": channel_scan,
        "inside_group": inside,
        "between_group": between,
        "split_file": split,
        "suggested_trim": suggested_trim,
        "output_dir": output_dir,
    }

    summary_text = build_summary_text(result)
    (output_dir / "summary.txt").write_text(summary_text, encoding="utf-8")

    log_func("Writing Excel and HTML reports...")
    excel_path = write_excel_report(result, output_dir)
    html_path = write_html_report(result, output_dir, summary_text)

    log_func("")
    log_func("Done.")
    log_func(f"Output folder: {output_dir}")
    log_func(f"Excel report: {excel_path}")
    log_func(f"HTML report: {html_path}")

    return result, excel_path, html_path, summary_text
