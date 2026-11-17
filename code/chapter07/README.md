# Chapter 7 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Hybrid retrieval, contextual chunks, reranking, citations, a jailed
grep/head search, and a three-way routing policy. Missing keys print one
line to stderr and the functions return fixed data. No client is built
at import.

## Setup

```bash
cd code/chapter07
uv sync
uv sync --all-groups
```

`uv sync --all-groups` installs the `ml` group, which holds
`sentence-transformers`. `hybrid_search` still returns a BM25 ranking
when that package is missing or the model weights cannot be downloaded.

## Run

```bash
uv run python listings/07-03-hybrid-rrf.py
uv run python listings/07-14-routing-policy.py
uv run pytest -q
```

## Expected offline output

`07-03-hybrid-rrf.py` prints the BM25 order when the embedding model
is unavailable:

```text
['doc-aisle', 'doc-window']
```

Stderr: `sentence-transformers model unavailable; returning BM25 order`.

`07-04-contextual-chunk.py` prints:

```text
Context from ACME Q2.

Revenue grew by 3 percent.
```

`07-05-cohere-rerank.py` prints `['a', 'b']`.

Stderr: `COHERE_API_KEY unset; returning input chunks unchanged`.

`07-07-citations.py` prints:

```text
growth?
ACME
```

`07-10-agentic-search.py` prints a line containing `aisle seat policy`.

`07-14-routing-policy.py` prints:

```text
static_hybrid
['gate change']
```

## Live API

Set `HARNESS_LIVE_API=1` plus the provider key (`ANTHROPIC_API_KEY` or
`COHERE_API_KEY`) before the live tests. The demos above do not call
the network.

## Listings

| File | What it shows |
| --- | --- |
| `listings/07-03-hybrid-rrf.py` | BM25, vectors, and reciprocal rank fusion |
| `listings/07-04-contextual-chunk.py` | A context sentence in front of a chunk |
| `listings/07-05-cohere-rerank.py` | Cross-encoder rerank, or the input order |
| `listings/07-07-citations.py` | An answer mapped back to source chunks |
| `listings/07-10-agentic-search.py` | Jailed grep and head over a corpus |
| `listings/07-14-routing-policy.py` | Static, graph, or agentic retrieval |
