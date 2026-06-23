# Reviewer guide

This guide is for someone reviewing the repository quickly, for example during a job application, collaboration discussion, code review, or portfolio assessment.

## 5-minute review path

1. Read the first sections of [`README.md`](../README.md).
2. Look at the workflow and report screenshots in `docs/assets/`.
3. Read [`portfolio_summary.md`](portfolio_summary.md).
4. Read [`validation_scope.md`](validation_scope.md) to understand what the tests prove and what they do not prove.
5. Inspect `src/tdms_sync_checker/core.py` for the metadata-first checks.
6. Inspect `tests/` to see how the main behaviours are protected.

## What to run locally

From the repository root:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

To check the CLI entry point:

```powershell
tdms-sync-checker --help
```

To open the GUI:

```powershell
python tdms_sync_checker_gui.py
```

## Public-safe synthetic example

The repository avoids real TDMS files. Generate a small synthetic TDMS file with:

```powershell
python examples/create_synthetic_tdms.py
```

Then run the checker:

```powershell
tdms-sync-checker `
  --input "examples/data/synthetic_tdms_reference.tdms" `
  --output "examples/outputs/synthetic_tdms_reference"
```

Review:

```text
examples/outputs/synthetic_tdms_reference/report.html
examples/outputs/synthetic_tdms_reference/summary.xlsx
examples/outputs/synthetic_tdms_reference/csv/
```

## What to look for in the code

| File or folder | What to review |
|---|---|
| `src/tdms_sync_checker/core.py` | TDMS scanning, timing checks, activity trim, report writing |
| `src/tdms_sync_checker/gui.py` | Threaded Tkinter GUI and report preview flow |
| `src/tdms_sync_checker/cli.py` | Command-line interface |
| `tests/` | Unit, smoke, and mocked integration tests |
| `.github/workflows/tests.yml` | CI workflow |
| `docs/validation_scope.md` | Test and validation boundary |
| `examples/create_synthetic_tdms.py` | Public-safe TDMS-like fixture generator |

## Interpretation notes

This tool is designed to flag metadata and timing issues for review. It does not automatically prove that all channels are physically synchronised. A real engineering workflow should still consider acquisition hardware, trigger configuration, clock drift, signal cross-correlation, known command events, and domain-specific timing tolerances.

## Suggested review questions

- Does the tool make minimal assumptions about channel names?
- Are outputs reviewable by an engineer?
- Are limitations stated clearly?
- Are tests focused on important behaviours?
- Is real or confidential data avoided?
- Is the project structure suitable for future extension?
