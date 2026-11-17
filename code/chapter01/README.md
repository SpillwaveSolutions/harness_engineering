# Chapter 1 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Two small pieces of the travel-booking agent, both offline.

- `listings/01-01-search-cap.py` walks a directory and refuses a search that returns more hits than `max_results`.
- `listings/01-02-travel-agent-skeleton.py` is the agent with a single `run` method and none of the later harness controls.

## Setup

```bash
cd code/chapter01 && uv sync --all-groups
```

## Run

```bash
uv run python listings/01-01-search-cap.py
```

```
ok
find a flight
```

```bash
uv run python listings/01-02-travel-agent-skeleton.py
```

```
I have booked your trip to Paris.
```

## Live calls

These two listings do not call a model. A live call elsewhere needs `HARNESS_LIVE_API=1` plus the provider key, usually `ANTHROPIC_API_KEY`.
