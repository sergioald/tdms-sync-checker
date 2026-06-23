# Portfolio summary

## Project in one sentence

**TDMS Sync Checker** is a metadata-first Python tool for reviewing TDMS acquisition structure, timing metadata, group/channel synchronisation, split-file continuity, inactive channels, and reportable data-quality issues in laboratory sensor datasets.

## Why this is useful

Large engineering experiments can produce TDMS files with many groups, channels, time bases, start times, sample counts, and acquisition sections. Before detailed signal analysis, digital-twin modelling, anomaly detection, or fatigue-test interpretation, the data often needs a basic QA/QC pass:

- Which groups and channels are present?
- Do channels inside a group share the same metadata timing?
- Do acquisition groups start at the same time or with systematic offsets?
- Do split files have gaps or overlaps?
- Which channels are changing, constant, mostly zero, or possibly inactive?
- What output can be reviewed by an engineer without opening the raw TDMS file manually?

This repository demonstrates a public, confidentiality-safe workflow for answering those questions.

## What the repository demonstrates

| Skill area | Evidence in the repository |
|---|---|
| Engineering data handling | TDMS metadata and channel scanning with `nptdms` |
| Time-series QA/QC | Start-time, sampling-interval, sample-count, duration, and overlap checks |
| Research software | Package structure, CLI, GUI, tests, CI, pre-commit, docs, changelog, licence |
| Reporting | CSV, Excel, HTML, and text outputs for reviewable engineering artefacts |
| Usability | Tkinter GUI for interactive use and CLI for repeatable execution |
| Public-safe communication | Synthetic/anonymised examples and explicit confidentiality boundaries |
| Validation awareness | Documentation that explains what the automated checks do and do not prove |

## Intended review audience

This project is useful for reviewers interested in:

- applied Python for engineering data;
- sensor-heavy laboratory workflows;
- QA/QC tooling for experimental datasets;
- scientific/research software engineering;
- data preparation for digital-twin or anomaly-detection workflows;
- practical tools that bridge GUI use and command-line automation.

## What is intentionally not included

The repository does not include real industrial or laboratory datasets, proprietary control logic, raw facility paths, partner data, or confidential test reports. Public examples are synthetic or anonymised. The synthetic TDMS generator imitates useful metadata patterns without reproducing real measured signals.

For details, see [`confidentiality_statement.md`](confidentiality_statement.md).

## Current maturity level

The repository is a prototype quality-control tool. It is suitable for exploratory TDMS metadata review and public portfolio demonstration. It is not yet a fully validated scientific synchronisation algorithm for every acquisition system.

The current test suite focuses on:

- pure timing/activity functions;
- CLI/import smoke checks;
- mocked full-pipeline report generation;
- CI execution across supported Python versions.

For details, see [`validation_scope.md`](validation_scope.md).

## Suggested reviewer path

A technical reviewer should start with:

1. [`README.md`](../README.md) for the overview and quick start.
2. [`reviewer_guide.md`](reviewer_guide.md) for a 5-minute review path.
3. [`validation_scope.md`](validation_scope.md) for the test/validation boundary.
4. `src/tdms_sync_checker/core.py` for the main metadata and report-generation logic.
5. `tests/` for the test design.
6. `examples/create_synthetic_tdms.py` for the public-safe synthetic TDMS example.

## Possible future extensions

High-value future improvements include:

- synthetic TDMS integration tests generated at test time;
- configurable thresholds through YAML or TOML;
- optional engineering diagnostics for cycle duration, command-response delay, and drift over time;
- richer HTML reports with summary warning levels;
- optional alignment-window export for downstream analysis.
