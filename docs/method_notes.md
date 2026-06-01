# Method Notes

## 1. Metadata scan

Each TDMS channel is inspected for:

- file name
- group name
- channel name
- reported start time
- reported `dt`
- reported sample rate
- sample count
- duration
- min, max, mean, standard deviation
- number of NaNs
- number of zero values
- changing/constant classification
- mostly-zero classification

## 2. Inside-group report

The inside-group report checks each file/group combination.

It reports whether the channels inside that group have:

- same start time
- same `dt`
- same number of samples

## 3. Between-group report

The between-group report estimates group-level timing:

- group start time
- group duration
- group end time
- offset from earliest group
- common overlap duration

This is useful when different acquisition systems or TDMS groups start at different times.

## 4. Split-file continuity

When a test is divided into multiple TDMS files, the tool:

1. groups files by a simple inferred test id
2. sorts sections by reported start time
3. estimates gap or overlap between consecutive sections

## 5. Suggested activity trim

The suggested activity trim is a heuristic. It estimates where the signal begins to differ from its initial baseline.

It does not assume that zero is invalid. This is important because zero can be a valid value in many command/state channels.

## 6. Plotting

Plotting is intentionally separated from the main GUI because large TDMS files can cause Matplotlib/Tkinter freezes.

Use the optional plotting script only after the metadata report is complete.
