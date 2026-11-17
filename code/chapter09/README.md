# Chapter 9 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Tool descriptions, a structured error, a schema-driven booking tool,
a code-as-action summary, and a registry that indexes tools and skills.
Nothing calls a model at import. A missing key prints one stderr line
and the function returns fixed data.

## Setup

```bash
cd code/chapter09
uv sync
```

## Run

```bash
uv run python listings/09-05-structured-error.py
uv run python listings/09-09-code-as-action.py
uv run python listings/09-16-capability-registry.py
uv run pytest -q
```

## Expected offline output

`09-02-tool-description.py` prints:

```text
True
True
```

`09-05-structured-error.py` prints:

```text
business
cancelled
```

`09-07-schema-driven-tool.py` prints:

```text
book_flight
success
```

Stderr: `ANTHROPIC_API_KEY unset; audit log stays local`.

`09-09-code-as-action.py` prints:

```text
offline: transferred 0 records (0 success, 0 errors)
```

Stderr: `ANTHROPIC_API_KEY unset; returning offline summary`.

`09-16-capability-registry.py` prints `flight-cancellation`.

## Live API

Set `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` to exercise the live
code-as-action call. The demos above do not call the network.

## Listings

| File | What it shows |
| --- | --- |
| `listings/09-02-tool-description.py` | Two tools that point at each other |
| `listings/09-05-structured-error.py` | Retryable vs business errors |
| `listings/09-07-schema-driven-tool.py` | Schema plus a local audit record |
| `listings/09-09-code-as-action.py` | A one-line migration summary |
| `listings/09-11-skill-md.txt` | Skill frontmatter the registry reads |
| `listings/09-16-capability-registry.py` | Register, discover, and dispatch |
