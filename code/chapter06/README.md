# Chapter 6 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

File-backed memory, a saliency score, and a Mem0-shaped extract/search
loop. Without API keys every listing stays on the machine: missing keys
print one line to stderr and the functions return fixed data.

## Setup

```bash
cd code/chapter06
uv sync
```

## Run

```bash
uv run python listings/06-03-mem0-extraction.py
uv run python listings/06-04-memory-directory.py
uv run python listings/06-06-saliency-eviction.py
uv run python listings/06-08-memory-subsystem.py
uv run pytest -q
```

## Expected offline output

`06-03-mem0-extraction.py` prints the stored turn, then the aisle hit:

```text
[{'memory': 'I prefer aisle seats.'}, {'memory': 'offline: noted the user turn'}]
['I prefer aisle seats.']
```

Stderr: `OPENAI_API_KEY unset; using in-memory memory` and
`ANTHROPIC_API_KEY unset; returning offline extraction`.

`06-04-memory-directory.py` prints:

```text
aisle seat
['preferences']
```

`06-06-saliency-eviction.py` prints:

```text
0.5
0.5
```

Stderr: `ANTHROPIC_API_KEY unset; returning offline importance 0.5`.

`06-08-memory-subsystem.py` prints:

```text
allergic to shellfish
['allergic to shellfish']
```

Stderr: `OPENAI_API_KEY unset; using in-memory memory`.

## Live API

Set `HARNESS_LIVE_API=1` plus `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`
to exercise Mem0 and the model. The demos above do not call the network.

## Listings

| File | What it shows |
| --- | --- |
| `listings/06-03-mem0-extraction.py` | Extract a turn, then search facts |
| `listings/06-04-memory-directory.py` | One markdown file per memory key |
| `listings/06-06-saliency-eviction.py` | Recency, worth, and eviction |
| `listings/06-08-memory-subsystem.py` | Provenance plus an audit log |
