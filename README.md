# TDMS Sync Checker

A metadata-first Python tool for checking TDMS file structure, timing metadata, group/channel synchronisation, split-file continuity, inactive channels, and suggested activity trimming.

> Status: **prototype / v0.1.0**  
> This tool was developed for exploratory laboratory TDMS quality control. Results should be reviewed by the user before they are used for engineering decisions.

## Why this tool exists

TDMS files can contain:

- different groups and channels from file to file
- different reported start times
- different sample rates
- different sample counts
- split sections due to file size
- inactive, constant, or mostly-zero channels
- possible start-up/buffer samples

This tool does **not** assume fixed channel names. It scans whatever is present and creates general QA/QC reports.

## Main features

- GUI for selecting one TDMS file or a folder of TDMS files
- command-line interface
- scans all TDMS groups and channels
- checks inside-group timing consistency
- checks between-group timing consistency
- checks split-file continuity
- identifies changing, constant, and mostly-zero channels
- estimates possible start/end activity trimming
- exports CSV, Excel, HTML, and plain-text summary files
- shows a GUI Report preview tab with the same main sections as the HTML report
- plotting is separated into an optional script to avoid GUI freezes with large files

## Installation

Create a virtual environment if possible, then install:

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Run the GUI

```bash
python tdms_sync_checker_gui.py
```

Or after installation:

```bash
tdms-sync-checker-gui
```

## Run from command line

Single TDMS file:

```bash
tdms-sync-checker --input "C:/path/to/file.tdms" --output "C:/path/to/output"
```

Folder of TDMS files:

```bash
tdms-sync-checker --input "C:/path/to/folder" --output "C:/path/to/output"
```

## Run in Spyder

Open and run:

```text
scripts/tdms_sync_checker_single_file_spyder.py
```

The GUI will open. After analysis, use the **Report preview** tab to review the main report inside the GUI, or click **Open HTML report in browser** for the fully formatted report.

## Outputs

The output folder contains:

```text
csv/
├── channel_metadata_all_channels.csv
├── inside_group_sync.csv
├── between_group_sync.csv
├── split_file_continuity.csv
└── suggested_activity_trim.csv

summary.xlsx
summary.txt
report.html
```

## Optional plotting

Plotting is intentionally separated from the main GUI to avoid freezing with large TDMS files.

After the main report works, edit and run:

```text
scripts/optional_tdms_plot_maker.py
```

Set:

```python
OUTPUT_FOLDER = Path(r"C:\Your\Folder\Here\tdms_general_sync_outputs")
```

Then run it. It creates downsampled plots in:

```text
optional_plots/
```

## Method summary

### Inside-group synchronisation

For each file/group combination, the tool checks whether all channels have:

- same reported start time
- same reported `dt`
- same sample count

### Between-group synchronisation

For each group, the tool estimates:

- group start time
- group duration
- group end time
- offset from earliest group
- common overlap duration

### Split-file continuity

For folders containing multiple `.tdms` files, the tool sorts sections by reported start time and checks for:

- continuous sections
- gaps
- overlaps

### Activity trimming

The suggested activity trim is only a **generic estimate**. It does not assume zero values are invalid, because zero can be a valid operating state.

## Limitations

- This is a metadata-first QA/QC tool, not a fully validated automatic synchronisation algorithm.
- TDMS metadata can be wrong or incomplete.
- Suggested trimming is heuristic and must be reviewed.
- Plotting is optional and separate because large TDMS files can overload Matplotlib/Tkinter.
- The tool does not replace engineering judgement.

## Repository structure

```text
tdms-sync-checker/
├── src/tdms_sync_checker/
│   ├── __init__.py
│   ├── core.py
│   ├── gui.py
│   ├── cli.py
│   └── __main__.py
├── scripts/
│   ├── optional_tdms_plot_maker.py
│   └── tdms_sync_checker_single_file_spyder.py
├── docs/
│   ├── method_notes.md
│   └── github_release_notes_v0.1.0.md
├── examples/
│   └── sample_output_description.md
├── tests/
├── tdms_sync_checker_gui.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Citation / acknowledgement

This project was developed as part of a laboratory workflow for TDMS data-quality checking and synchronisation review.
