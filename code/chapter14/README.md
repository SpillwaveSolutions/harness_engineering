# Chapter 14 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Evaluator-optimizer loop, judge rubric, browser check, calibration,
stratified sampling, message batches, and the four-lane promotion gate.

Importing a listing does not read required environment variables and does
not open a network connection. Paid model calls and the browser check stay
off unless `HARNESS_LIVE_API=1`.

## Setup

```bash
cd code/chapter14
uv sync --all-groups
```

## Tests

```bash
uv run pytest
```

## Run

The promotion-gate script requires two JSON paths. With no arguments it
exits 2 and prints a usage line:

```bash
uv run python listings/14-09-gate-script.py
```

Expected stderr (exit code 2):

```
usage: 14-09-gate-script.py [-h] --baseline-scores BASELINE_SCORES --eval-dataset EVAL_DATASET
```

Offline browser check:

```bash
uv run python -c 'import importlib.util; p="listings/14-03-browser-assertion.py"; s=importlib.util.spec_from_file_location("b", p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.verify_booking_ui("AA100", "Ada Lovelace"))'
```

Expected stderr:

```
offline: HARNESS_LIVE_API is not 1; browser not started
```

Expected stdout:

```
{'status': 'offline', 'flight_id': 'AA100', 'passenger_name': 'Ada Lovelace'}
```

Set `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` before a live model call.
The browser check also needs `HARNESS_LIVE_API=1` and a local browser
runtime; it is not started on import.
