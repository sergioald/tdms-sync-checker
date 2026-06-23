# Validation scope

This document explains what the current test suite checks, what it does not prove, and how the results should be interpreted.

## Purpose

`tdms-sync-checker` is a metadata-first QA/QC tool for reviewing TDMS timing metadata, group/channel consistency, split-file continuity, channel activity, and report generation.

The tests are designed to protect the software behaviour of the repository. They are not a substitute for engineering validation of a specific laboratory acquisition system, sensor configuration, control sequence, or TDMS export workflow.

## Current test levels

### Unit tests

The unit tests cover deterministic functions that can be checked without real TDMS files, including:

- channel-name normalisation;
- basic signal statistics;
- suggested activity-trim logic;
- inside-group timing consistency checks;
- between-group timing offset and common-overlap calculations;
- split-file continuity classification.

These tests are intended to catch regressions in the core table-building and metadata-interpretation logic.

### Smoke tests

The smoke tests check that:

- the package imports;
- the core module imports;
- the GUI module imports without starting the interface;
- the CLI help command can run without a TDMS file.

These tests are intentionally lightweight. They provide early warning when packaging, imports, or entry points are broken.

### Mocked integration test

The current integration test exercises the full `run_analysis` report-generation pathway using a mocked TDMS scan. It checks that the analysis pipeline can produce:

- CSV outputs;
- an Excel summary;
- an HTML report;
- a plain-text summary.

This keeps the test suite safe for public use because it does not require real laboratory TDMS data.

## What the tests do not prove

The tests do not prove that:

- TDMS metadata are always correct;
- all TDMS exporters store timing metadata in the same way;
- all channels are physically synchronised in the acquisition hardware;
- a detected common overlap is physically meaningful for every test rig;
- suggested activity trimming is always the correct engineering choice;
- zero values are invalid;
- constant channels are faulty;
- split-file names always represent the real acquisition order;
- the GUI is fully tested under all operating systems;
- the tool is a validated automatic synchronisation algorithm.

The repository should therefore describe the software as a QA/QC and review tool, not as a definitive synchronisation-correction method.

## Why real TDMS files are not included

Real TDMS files may contain sensitive information, including:

- laboratory paths and machine names;
- facility-specific group/channel names;
- acquisition settings;
- control-system behaviour;
- partner or industrial data;
- operational test sequences.

For public testing, the preferred approach is to use small synthetic fixtures, mocked readers, or anonymised metadata tables.

## Recommended interpretation

A passing test suite means that the repository's implemented software checks behave as expected on controlled examples. It does not mean that a particular experimental dataset is synchronised, physically valid, or ready for engineering decisions.

Outputs from this tool should always be reviewed with knowledge of the acquisition system, sensor layout, sampling strategy, and test procedure.

## Future validation work

Useful next additions would be:

- tiny synthetic TDMS fixtures generated during testing;
- regression tests for known anonymised edge cases;
- CLI tests that run on generated fixture files;
- optional GUI interaction tests for critical buttons and state transitions;
- documented comparison against manually inspected laboratory examples;
- benchmark notes for large TDMS files.
