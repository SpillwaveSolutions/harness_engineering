# Chapter 13 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Observability listings for the travel-booking agent: OpenTelemetry spans,
a Langfuse exporter setup, an offline judge, and a promotion gate.
Importing a listing does not read exporter endpoints, start a batch span
processor, or construct a Langfuse or LangSmith client.

| File | What it does |
| --- | --- |
| `listings/13-01-otel-model-span.py` | `call_model_with_span(messages, conversation_id)` records a chat span. Missing endpoint uses an in-memory exporter. Missing API key returns a fake response. |
| `listings/13-02-seven-span-kinds.py` | `run_booking_step()` nests a model span and a tool span and returns a dict. |
| `listings/13-03-span-attributes.py` | `record_cost()` and `record_eval_verdict()` set span attributes. |
| `listings/13-04-trace-query.txt` | SQL that filters tool spans for one conversation. |
| `listings/13-05-langfuse-setup.py` | `setup_langfuse()` returns `None` unless both Langfuse keys are set. |
| `listings/13-06-cost-query.txt` | SQL cost rollup. |
| `listings/13-06b-cost-promql.promql` | PromQL token-rate sketch. |
| `listings/13-08-llm-judge-calibrated.py` | `score_booking_response()` uses an offline judge when the API key is unset. |
| `listings/13-09-promotion-gate.py` | `run_promotion_gate()` compares scores. Without a LangSmith key it uses an in-memory table. |

## Setup

```bash
cd code/chapter13
uv sync --all-groups
```

## Run offline

```bash
uv run python listings/13-01-otel-model-span.py
uv run python listings/13-02-seven-span-kinds.py
uv run python listings/13-05-langfuse-setup.py
uv run python listings/13-08-llm-judge-calibrated.py
uv run python listings/13-09-promotion-gate.py exp-baseline 42
```

Expected offline output:

```text
input_tokens=12 output_tokens=8
{'conversation_id': 'conv-offline', 'status': 'ok', 'tools': [{'status': 'ok', 'tool': 'search_flights', ...}]}
offline
{"score": 4, "label": "PASS", "explanation": "Offline judge: booking looks valid."}
```

`13-09` with both arguments exits 0 because the in-memory scores clear
the floors. With no arguments it prints a usage line and exits 2.

Stderr names the missing variable (`OTEL_EXPORTER_OTLP_ENDPOINT`,
`ANTHROPIC_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, or
`LANGSMITH_API_KEY`).

## Tests

```bash
uv run pytest -q
```

Tests call the functions and assert the offline results. They do not
skip on import errors.

## Live calls

Set `HARNESS_LIVE_API=1` plus the keys named above to export spans, call
the model, or read a LangSmith experiment. The default test run leaves
those unset.
