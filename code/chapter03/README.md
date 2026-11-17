# Chapter 3 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

A Strands booking hook and three LangGraph workflow shapes: a fixed prompt chain, orchestrator-workers, and an evaluator-optimizer loop. The model steps are local stand-ins, so the graphs run without a network call.

- `listings/03-06-strands-hook.py` blocks `book_flight` when `passenger_count` is above 10.
- `listings/03-09-prompt-chain.py` cleans a document, extracts fields, then writes a compliance report.
- `listings/03-12-orchestrator-workers.py` plans tasks, runs them, and joins the outputs.
- `listings/03-13-evaluator-optimizer.py` drafts, scores, and revises until the draft passes or the iteration cap is hit.

## Setup

```bash
cd code/chapter03 && uv sync --all-groups
```

The hook imports `strands` from the `strands-agents` package.

## Run

```bash
uv run python listings/03-06-strands-hook.py
```

```
BLOCKED: maximum passenger limit is 10, received 11.
```

```bash
uv run python listings/03-09-prompt-chain.py
```

```
Borrower: Ada Lovelace
PASS: all compliance rules satisfied.
```

```bash
uv run python listings/03-12-orchestrator-workers.py
```

```
output for: investigate: login fails
```

```bash
uv run python listings/03-13-evaluator-optimizer.py
```

```
True
2
revised draft addressing: draft needs improvement
```

## Live calls

These listings do not call a model. A live call elsewhere needs `HARNESS_LIVE_API=1` plus the provider key, usually `ANTHROPIC_API_KEY`.
