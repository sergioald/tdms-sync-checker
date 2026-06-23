# Changelog

## Unreleased

### Added

- Unit tests for important pure functions in the TDMS metadata QA/QC workflow.
- Smoke tests for package imports, GUI-module import, and CLI help execution.
- A mocked full-pipeline integration test that exercises report generation without requiring real TDMS data.
- GitHub Actions CI for pre-commit checks and pytest on Python 3.10, 3.11, and 3.12.
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
