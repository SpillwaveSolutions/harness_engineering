# Chapter 5 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Context-window controls for the travel agent: trim a flight result, cap a large search, extract facts, and assemble a payload under a token budget.

- `listings/05-07-boundary-trim.py` keeps five flight fields and drops the rest.
- `listings/05-07-search-cap.py` rejects a result set larger than 50.
- `listings/05-08-fact-extraction.py` reads dates and dollar amounts from the message when it is offline.
- `listings/05-09-context-manager.py` orders context slots and enforces a token budget. The client is injected by the caller; import does not build one.

## Setup

```bash
cd code/chapter05 && uv sync --all-groups
```

## Run

```bash
uv run python listings/05-07-boundary-trim.py
```

```
UA1182 312
False
```

```bash
uv run python listings/05-07-search-cap.py
```

```
too_many_results
51
51 flights matched SFO->JFK. Add a time window or fare class.
```

```bash
uv run python listings/05-08-fact-extraction.py
```

stdout:

```
[{'date': 'June 15, 2026'}, {'amount': '$127.50'}]
PERSISTENT FACTS (do not paraphrase, do not compress):
  date: June 15, 2026
  amount: $127.50
```

stderr:

```
offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY to extract facts with the model.
```

```bash
uv run python listings/05-09-context-manager.py
```

```
500
origin: SFO

You book travel.
Book a flight to Tokyo.
```

## Live calls

`extract_facts_from_turn` calls the model only when `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` are both set. Otherwise it prints one stderr line and returns fact dicts parsed from the message text. The other listings do not call the network.
