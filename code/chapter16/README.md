# Chapter 16 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Prompt-injection defenses for tool output, memory writes, signed agent
cards, and the harness wiring that ties them together. The included
harness does not call a model.

`python listings/<file>.py` puts `listings/` on `sys.path`. Each listing
that imports `harness` inserts the chapter root
(`Path(__file__).resolve().parents[1]`) before that import.

## Setup

```bash
cd code/chapter16
uv sync --all-groups
```

## Tests

```bash
uv run pytest
```

## Run

```bash
uv run python listings/16-01-prompt-injection-chain-failing-test.py
```

Expected result: no stdout, exit code 0. The injected vendor note does not
land in memory.

`HARNESS_LIVE_API=1` is not used here. These listings stay offline.
