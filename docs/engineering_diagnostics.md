# Engineering diagnostics

`tdms-sync-checker` is primarily a metadata-first TDMS QA/QC tool. The engineering diagnostics introduced for `v0.3.0` are optional signal-level helpers for cases where the user already knows which command and response channels should be compared.

These diagnostics are intended for review questions such as:

- How many command or trigger cycles are visible?
- Is the command-cycle duration stable across the test?
- What is the delay between a command transition and a response transition?
- Does the response delay drift as the test progresses?
- Is there a common active window between selected channels?

They are deliberately conservative and do not replace engineering judgement.

---

## Typical use case

A laboratory TDMS acquisition may contain channels such as:

```text
FD command / trigger signal
shaft speed or CAN signal
hydraulic pressure
inverter power
accumulator pressure
load or displacement channel
```

The metadata-first report can show whether groups and channels have consistent reported timestamps, sampling intervals, and sample counts. The optional engineering diagnostics go one step further by comparing selected signal transitions.

---

## Command-line example

After creating or selecting a TDMS file, run:

```powershell
python scripts/run_engineering_diagnostics.py `
  --input "examples/data/synthetic_tdms_reference.tdms" `
  --output "examples/output_engineering_diagnostics" `
  --command-channel "FD_Command" `
  --response-channel "Inverter_Power" `
  --command-direction rising `
  --response-direction rising `
  --max-delay-s 2.0 `
  --make-plots
```

If channel names are ambiguous, provide group filters:

```powershell
python scripts/run_engineering_diagnostics.py `
  --input "C:/path/to/file.tdms" `
  --output "C:/path/to/output" `
  --command-group "Group 6" `
  --command-channel "FdLimited" `
  --response-group "Group 3" `
  --response-channel "Power" `
  --max-delay-s 2.0
```

Channel matching uses the normalised channel name, where text after a newline suffix is ignored. This helps with TDMS exports where a channel name may contain extra units or comments after a line break.

---

## Outputs

The diagnostic output folder contains:

```text
selected_channels.csv
engineering_diagnostic_summary.txt
csv/
├── command_edges.csv
├── response_edges.csv
├── cycle_duration_stability.csv
└── response_delays.csv
figures/
├── cycle_duration_stability.png
└── response_delay.png
```

The figure folder is created only when `--make-plots` is used.

---

## Method summary

### 1. Edge detection

The selected command and response channels are converted to one-dimensional numeric arrays. A threshold is either supplied by the user or estimated as the midpoint between low and high robust quantiles.

The script can detect:

- rising edges;
- falling edges;
- both rising and falling edges.

A minimum interval can be applied to command edges to avoid double-counting noisy threshold crossings.

### 2. Cycle duration

Command cycles are estimated from repeated command edges. For a binary trigger or command signal, this is usually rising-edge to rising-edge duration.

The output table reports:

- cycle index;
- start time;
- end time;
- duration;
- start/end sample indices.

### 3. Command-response delay

Each command edge is matched to the first later response edge. A maximum delay can be supplied to avoid matching unrelated later events.

The output table reports:

- command event index;
- command time;
- response time;
- delay;
- whether a response was matched.

### 4. Delay drift

A simple linear trend is estimated across matched delays. This is a diagnostic indicator only. It can help identify whether command-response delay grows or shrinks over the test.

---

## Interpretation guidance

A stable acquisition should usually show:

- a plausible number of command cycles;
- cycle durations that are close to the expected operating cycle;
- response delays that remain broadly stable;
- no strong systematic drift in response delay.

However, apparent instability may come from:

- incorrect channel selection;
- wrong edge direction;
- poor threshold choice;
- real signal noise;
- channels with different sampling rates;
- channels that encode state differently from a simple threshold crossing;
- real physical/control changes rather than synchronisation drift.

Always review diagnostic plots and the original signals before drawing engineering conclusions.

---

## What these diagnostics do not prove

These diagnostics do **not** prove that a TDMS acquisition is synchronised. They also do not prove that a delay is caused by instrumentation, control-system behaviour, physical response, or post-processing artefacts.

They provide practical evidence for engineering review by making timing relationships visible and repeatable.

For validation scope, see [`validation_scope.md`](validation_scope.md).
