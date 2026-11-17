# AI Harness Engineering — companion code

Runnable listings for the book, one directory per chapter.

```
code/chapter01/listings/   chapter 1
code/chapter02/listings/   chapter 2
...
code/chapter17/listings/   chapter 17
```

Chapter numbers are zero-padded (`chapter01`, not `chapter1`).

## Setup

Python 3.13 or newer, and [uv](https://docs.astral.sh/uv/).

```bash
cd code/chapterNN
uv sync --all-groups
```

`--all-groups` installs the chapter's runtime libraries, pytest, and the
optional heavy extras (sentence-transformers in chapter 07).

The code is under the MIT license in `LICENSE` (Copyright (c) 2026
Spillwave Solutions).

Listings read process environment variables. They do not load
`code/.env`. Export the variables yourself before a live run.
`code/.env.example` lists the names.

## Run a listing

From the chapter directory:

```bash
uv run python listings/NN-MM-slug.py
```

With API keys unset, each script prints a short offline result and exits 0.
It does not crash at import time.

## Tests

```bash
cd code/chapterNN
uv run pytest -q
```

Tests call the listings in offline mode. Tests that talk to a paid API are
skipped unless you set `HARNESS_LIVE_API=1` and the keys named in that
chapter's README.

## Keys

| Variable | Used by |
|---|---|
| `ANTHROPIC_API_KEY` | chapters that call the model API |
| `OPENAI_API_KEY` | chapter 06 memory extraction |
| `COHERE_API_KEY` | chapter 07 rerank |
| `LANGFUSE_*` | chapter 13 trace export |
| `LANGSMITH_API_KEY` | chapter 13 promotion gate |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | chapter 13 span export |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | chapter 10 sandbox demo |
| `HARNESS_LIVE_API=1` | turns on the live-API tests |
