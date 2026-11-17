# Chapter 2 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

The naked travel loop, the same loop with three controls, and a recorded span for a booking that failed while the outer turn stayed OK.

- `listings/02-01-naked-travel-agent.py` defines `dispatch` and `run_naked`.
- `listings/02-02-three-controls.py` validates tool arguments, trims history, and records an OpenTelemetry span around each tool call. No exporter endpoint is required to import it.
- `listings/02-03-failure-catch.py` builds the span tree for a failed `book_flight`.

## Setup

```bash
cd code/chapter02 && uv sync --all-groups
```

## Run

```bash
uv run python listings/02-01-naked-travel-agent.py
```

stdout:

```
offline reply: Book a flight from SFO to JFK.
```

stderr:

```
offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY to call the model.
```

```bash
uv run python listings/02-02-three-controls.py
```

stdout:

```
valid=True reason=''
offline reply: Book a flight to Lisbon.
```

stderr:

```
offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY to call the model.
```

```bash
uv run python listings/02-03-failure-catch.py
```

```
{
  "name": "agent.turn",
  "status": "OK",
  "children": [
    {
      "name": "model.call",
      "status": "OK",
      "children": []
    },
    {
      "name": "tool.book_flight",
      "status": "ERROR",
      "attributes": {
        "tool.success": false,
        "tool.error": "Seat unavailable on flight AA1234",
        "flight_id": "AA1234"
      },
      "exception": "ValueError('Seat unavailable on flight AA1234')"
    },
    {
      "name": "model.call",
      "status": "OK",
      "children": []
    }
  ]
}
```

## Live calls

`run_naked` and `run_harnessed` call the model only when `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` are both set. Otherwise each prints one stderr line and returns `offline reply:` plus the user text. Importing the files does not build a client.
