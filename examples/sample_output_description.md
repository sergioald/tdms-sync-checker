# Example Output Description

After running the tool, the output folder should contain:

```text
csv/
summary.xlsx
summary.txt
report.html
```

The most important files are:

- `summary.txt`: quick human-readable overview
- `summary.xlsx`: all tables in one workbook
- `report.html`: browser-readable report
- `csv/channel_metadata_all_channels.csv`: all file/group/channel metadata
- `csv/inside_group_sync.csv`: inside-group timing consistency
- `csv/between_group_sync.csv`: between-group timing consistency
- `csv/split_file_continuity.csv`: split-file gap/overlap check
- `csv/suggested_activity_trim.csv`: generic suggested activity trim
