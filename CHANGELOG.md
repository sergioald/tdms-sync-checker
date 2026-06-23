# Changelog

## Unreleased

### Added

- Optional engineering diagnostics module for selected command/response channels.
- Threshold-based edge detection for command and response signals.
- Command-cycle duration estimation and stability summaries.
- Command-response delay matching and delay-drift summaries.
- Common active-window helper functions for selected channels.
- Optional diagnostic plotting helpers for cycle duration and response delay.
- `scripts/run_engineering_diagnostics.py` for running the new diagnostics on a selected TDMS file.
- `docs/engineering_diagnostics.md` explaining usage, outputs, interpretation, and validation limitations.
- Unit tests for the new engineering diagnostic functions.

## v0.2.1

Documentation polish and synthetic TDMS example.

- Improved reviewer-facing README structure.
- Added portfolio summary documentation.
- Added reviewer guide.
- Added confidentiality statement.
- Added synthetic TDMS reference summary.
- Added reproducible synthetic TDMS example scripts.

## v0.2.0

Tests, CI, pre-commit, and validation notes.

- Unit tests for important pure functions in the TDMS metadata QA/QC workflow.
- Smoke tests for package imports, GUI-module import, and CLI help execution.
- Mocked full-pipeline integration test that exercises report generation without requiring real TDMS data.
- GitHub Actions CI for pre-commit checks and pytest.
- Local pre-commit configuration using Ruff.
- Validation-scope documentation explaining what the tests do and do not prove.

## v0.1.0

Initial prototype release.

- Metadata-first TDMS QA/QC checker
- GUI and CLI
- Inside-group timing report
- Between-group timing report
- Split-file continuity report
- Activity classification
- Suggested activity trim
- CSV, Excel, HTML, and TXT output
- GUI Report preview tab
- Buttons for opening HTML report and output folder
- Optional plotting script outside the main GUI
