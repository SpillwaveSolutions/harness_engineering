# Chapter 17 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Pattern coverage table, in-process tool registration, a migration diff,
a YAML cost model, and a quarterly model-swap rehearsal.

Importing a listing does not call `query` and does not require credentials.
`create_deep_agent` builds a local graph and does not contact a provider.
Tool functions return an offline booking reference. The rehearsal reads a
missing eval set or baseline as empty and returns a deterministic verdict.

## Setup

```bash
cd code/chapter17
uv sync --all-groups
```

## Tests

```bash
uv run pytest
```

## Run

```bash
uv run python listings/17-11-model-swap.py
```

Expected stdout:

```
SKIPPED: no evals run for claude-sonnet-4-7
```

The process exits 2. Expected stderr (the eval set is not in the tree):

```
SKIPPED: eval set evals/travel_booking_v3.jsonl is missing; no evals run
```

Exit code 0.

Offline tool call:

```bash
uv run python -c 'import asyncio, importlib.util; p="listings/17-05-deepagents-registry.py"; s=importlib.util.spec_from_file_location("d", p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(asyncio.run(m.book_flight("AA100", "Ada Lovelace")))'
```

Expected stdout:

```
{'status': 'offline', 'reference': 'OFFLINE-BOOKING', 'flight_id': 'AA100', 'passenger_name': 'Ada Lovelace'}
```

Set `HARNESS_LIVE_API=1` before `run_agent` or `run_after_migration` if you
want those functions to call `query`. The rehearsal helpers stay offline.
