# Test suite

This folder contains the first public test suite for `tdms-sync-checker`.

The current tests are intentionally lightweight and confidentiality-safe:

- `test_activity_trim.py` checks pure signal/statistics helpers.
- `test_timing_checks.py` checks inside-group and between-group metadata logic.
- `test_split_file_continuity.py` checks split-file ordering and gap/overlap classification.
- `test_imports_and_cli.py` provides smoke tests for imports and CLI help.
- `test_pipeline_integration.py` exercises report generation using a mocked TDMS scan.

Run locally with:

```bash
python -m pip install -e ".[dev]"
pytest
```

Run pre-commit locally with:

```bash
pre-commit run --all-files
```

For interpretation limits, see `docs/validation_scope.md`.
