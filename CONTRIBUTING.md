# Contributing

This is currently a prototype research/laboratory tool.

## Development setup

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

## Style check

```bash
ruff check .
```

## Reporting issues

When reporting a problem, include:

- operating system
- Python version
- whether you used GUI or CLI
- whether the input was one file or a folder
- number of TDMS files
- approximate number of groups/channels
- the error shown in the GUI log
