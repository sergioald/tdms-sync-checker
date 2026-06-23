# Changelog

## Unreleased

### Added

- Portfolio-oriented README polish with clearer reviewer positioning, Anaconda/Windows quick start, testing commands, and synthetic-example usage.
- `docs/portfolio_summary.md` describing the repository as a public engineering-data QA/QC and research-software artefact.
- `docs/reviewer_guide.md` with a short path for technical reviewers, recruiters, and collaborators.
- `docs/confidentiality_statement.md` clarifying what must not be committed and how public-safe examples should be prepared.
- `docs/synthetic_tdms_reference_summary.md` documenting the public-safe synthetic TDMS metadata pattern.
- `examples/create_synthetic_tdms.py` for generating a small synthetic TDMS file without real laboratory data.
- `examples/run_synthetic_example.py` for generating the synthetic file and running the checker on it.

### Notes

- The synthetic TDMS example imitates metadata structure only. It does not copy measured data, confidential facility behaviour, or proprietary control logic.
- This documentation-focused update does not change the core TDMS synchronisation algorithm.

## v0.2.0

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
