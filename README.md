# TDMS Sync Checker

[![Tests](https://github.com/sergioald/tdms-sync-checker/actions/workflows/tests.yml/badge.svg)](https://github.com/sergioald/tdms-sync-checker/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-prototype%20v0.2-orange.svg)
![Release](https://img.shields.io/github/v/release/sergioald/tdms-sync-checker)

A **metadata-first Python tool** for checking TDMS file structure, timing metadata, group/channel synchronisation, split-file continuity, inactive channels, and suggested activity trimming.

It is designed for exploratory laboratory TDMS quality control where large files can make full plotting slow or unstable. The main GUI therefore focuses on metadata checks and reviewable reports; plotting is available as a separate optional step.

<p align="center">
  <img src="docs/assets/readme_gui_analysis_complete.png" alt="TDMS Sync Checker GUI showing completed analysis" width="900">
</p>

<p align="center">
  <em>GUI workflow after a completed metadata-first TDMS synchronisation check. Example paths and data shown in screenshots are anonymised or synthetic.</em>
</p>

> **Status:** prototype / v0.2  
> Results should be reviewed by the user before they are used for engineering decisions.

---

## Why this project exists

TDMS files from laboratory systems can contain many acquisition groups, channel naming conventions, timestamps, sampling rates, sample counts, split-file sections, inactive channels, and start-up/buffer samples.

This repository provides a public, confidentiality-safe QA/QC workflow for reviewing those metadata and timing issues before deeper engineering analysis. It is intended for:

- laboratory data-quality checks;
- TDMS acquisition reviews;
- sensor-heavy engineering workflows;
- reproducible research-software demonstration;
- portfolio review without exposing real facility data.

The tool does **not** assume fixed channel names. It scans whatever is present and creates general QA/QC reports.

For a reviewer-facing explanation, see [`docs/portfolio_summary.md`](docs/portfolio_summary.md). For what the tests do and do not prove, see [`docs/validation_scope.md`](docs/validation_scope.md). For confidentiality boundaries, see [`docs/confidentiality_statement.md`](docs/confidentiality_statement.md).

---

## What this repository demonstrates

| Area | What is demonstrated |
|---|---|
| TDMS handling | Metadata and channel scanning across real-world TDMS-style group structures |
| Timing QA/QC | Inside-group, between-group, and split-file timing consistency checks |
| Engineering reporting | CSV, Excel, HTML, and plain-text outputs for reviewable QA/QC artefacts |
| GUI usability | A Tkinter desktop interface for non-command-line review workflows |
| CLI usability | Repeatable command-line execution for automated or scripted checks |
| Public-safe examples | Synthetic/anonymised examples instead of real laboratory data |
| Research software | Package structure, tests, CI, pre-commit, docs, limitations, and validation notes |

---

## Workflow overview

<p align="center">
  <img src="docs/assets/readme_workflow.png" alt="TDMS metadata QA/QC workflow" width="900">
</p>

The core workflow is:

```text
TDMS file or folder
→ metadata scan across groups/channels
→ inside-group synchronisation checks
→ between-group timing checks
→ split-file continuity checks
→ activity/trim summary
→ CSV, Excel, HTML, and text outputs
```

---

## Quick start

### Option A: Windows / Anaconda PowerShell Prompt

```powershell
conda create -n tdms_sync python=3.10 -y
conda activate tdms_sync

git clone https://github.com/sergioald/tdms-sync-checker.git
cd tdms-sync-checker

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

Run the GUI:

```powershell
python tdms_sync_checker_gui.py
```

Or, after installation:

```powershell
tdms-sync-checker-gui
```

### Option B: Standard Python environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

---

## Command-line usage

Single TDMS file:

```bash
tdms-sync-checker --input "C:/path/to/file.tdms" --output "C:/path/to/output"
```

Folder of TDMS files:

```bash
tdms-sync-checker --input "C:/path/to/folder" --output "C:/path/to/output"
```

PowerShell line-continuation example:

```powershell
tdms-sync-checker `
  --input "C:/path/to/folder" `
  --output "C:/path/to/output"
```

---

## Spyder / Anaconda workflow

Open and run:

```text
scripts/tdms_sync_checker_single_file_spyder.py
```

The GUI will open. After analysis, use the **Report preview** tab to review the main summary inside the GUI, or click **Open HTML report in browser** for the full report.

---

## Synthetic TDMS example

The repository avoids committing real laboratory TDMS data. To support public testing and demonstration, a small synthetic TDMS generator is provided:

```powershell
python examples/create_synthetic_tdms.py
```

This creates:

```text
examples/data/synthetic_tdms_reference.tdms
```

Then run the checker on the generated file:

```powershell
tdms-sync-checker `
  --input "examples/data/synthetic_tdms_reference.tdms" `
  --output "examples/outputs/synthetic_tdms_reference"
```

The synthetic file is not real facility data. It only imitates useful public-safe metadata patterns such as multiple acquisition groups, mixed sample rates, timestamp channels, CAN-style channel names, inactive channels, and small timing offsets.

For details, see [`docs/synthetic_tdms_reference_summary.md`](docs/synthetic_tdms_reference_summary.md).

---

## Example HTML report

<p align="center">
  <img src="docs/assets/readme_html_report_overview.png" alt="Generated TDMS synchronisation HTML report" width="900">
</p>

<p align="center">
  <em>Generated HTML report with executive summary, inside-group checks, between-group synchronisation, and split-file continuity tables. Example paths and file names are anonymised or synthetic.</em>
</p>

---

## Outputs

The output folder contains machine-readable tables and human-readable summaries:

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

| Output | Purpose |
|---|---|
| `channel_metadata_all_channels.csv` | Full channel-level metadata table |
| `inside_group_sync.csv` | Per-file/per-group checks for start time, `dt`, and sample-count consistency |
| `between_group_sync.csv` | Group-level timing offsets, durations, and common-overlap estimates |
| `split_file_continuity.csv` | Gap/overlap checks for multi-file acquisitions |
| `suggested_activity_trim.csv` | Generic suggested start/end trimming estimates |
| `summary.xlsx` | Spreadsheet version of the report tables |
| `summary.txt` | Plain-text executive summary |
| `report.html` | Browser-readable report |

---

## Method summary

### Inside-group synchronisation

For each file/group combination, the tool checks whether all channels have:

- the same reported start time;
- the same reported `dt`;
- the same sample count.

### Between-group synchronisation

For each group, the tool estimates:

- group start time;
- group duration;
- group end time;
- offset from the earliest group;
- common overlap duration.

### Split-file continuity

For folders containing multiple `.tdms` files, the tool sorts sections by reported start time and checks for:

- continuous sections;
- gaps;
- overlaps.

### Activity trimming

The suggested activity trim is a **generic estimate**. It does not assume that zero values are invalid, because zero can be a valid operating state.

---

## Tests and quality checks

Run the test suite:

```powershell
python -m pytest
```

Run Ruff manually:

```powershell
python -m ruff check .
```

Run pre-commit locally:

```powershell
pre-commit install
pre-commit run --all-files
```

The current tests cover pure timing/activity functions, import/CLI smoke checks, and a mocked report-generation pipeline. They do not prove scientific synchronisation validity against every possible TDMS acquisition system. See [`docs/validation_scope.md`](docs/validation_scope.md).

---

## Optional plotting

Plotting is intentionally separated from the main GUI to avoid freezing with large TDMS files.

After the main report works, edit and run:

```text
scripts/optional_tdms_plot_maker.py
```

Set the output folder in the script:

```python
OUTPUT_FOLDER = Path(r"C:\Your\Folder\Here\tdms_general_sync_outputs")
```

Then run it. It creates downsampled plots in:

```text
optional_plots/
```

---

## Limitations

- This is a metadata-first QA/QC tool, not a fully validated automatic synchronisation algorithm.
- TDMS metadata can be wrong, incomplete, or inconsistent with the actual sensor data.
- Suggested trimming is heuristic and must be reviewed.
- Plotting is optional and separate because large TDMS files can overload Matplotlib/Tkinter.
- The tool does not replace engineering judgement.

---

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
│   ├── assets/
│   ├── confidentiality_statement.md
│   ├── method_notes.md
│   ├── portfolio_summary.md
│   ├── reviewer_guide.md
│   ├── synthetic_tdms_reference_summary.md
│   └── validation_scope.md
├── examples/
│   ├── create_synthetic_tdms.py
│   └── sample_output_description.md
├── tests/
├── tdms_sync_checker_gui.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

---

## Citation / acknowledgement

This project was developed as part of a laboratory workflow for TDMS data-quality checking and synchronisation review.

---

## License

See [`LICENSE`](LICENSE).
