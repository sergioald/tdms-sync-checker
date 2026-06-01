# Release Notes - v0.1.0

Initial prototype release.

## Added

- General TDMS metadata scanner
- Tkinter GUI
- CLI entry point
- Inside-group timing report
- Between-group timing report
- Split-file continuity report
- Channel activity classification
- Suggested activity trim report
- CSV, Excel, HTML and TXT outputs
- GUI Report preview tab and buttons to open the HTML report/output folder
- Optional separate plotting script

## Known limitations

- Plotting is not integrated into the main GUI because large TDMS files can freeze the interface.
- Suggested activity trim is heuristic.
- Synchronisation is metadata-based and should be reviewed by the user.
