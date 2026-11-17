# Chapter 8 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Schema checks, spend and tool policy, and pre/post tool hooks for the
agent SDK and for LangChain middleware. Options objects use fields the
SDK accepts. Tool functions return fixed offline data. Nothing dials
the network at import.

## Setup

```bash
cd code/chapter08
uv sync
```

## Run

```bash
uv run python listings/08-03-claude-tool-choice.py
uv run python listings/08-07-date-normalize.py
uv run pytest -q
```

## Expected offline output

`08-03-claude-tool-choice.py` prints:

```text
OFFLINE-DEMO
AA100
book_flight
ClaudeSDKClient
```

`08-04-semantic-validator.py` prints `AA100`.

`08-05-claude-policy.py` prints:

```text
50.0
delete_booking
```

`08-06-claude-prehook.py` prints `deny`.

`08-07-claude-posthook.py` prints:

```text
card 411111××××××1111 ssn [SSN REDACTED]
```

`08-07-date-normalize.py` prints `2026-05-15`.

`08-08-validation-retry.py` prints `accepted`.

`08-10-claude-integrated.py` prints `booked AA100`.

The LangChain listings print an `OFFLINE-DEMO` booking reference or an
`offline:` search string, plus numeric call limits where the file sets
them (`20` and `50`).

## Live API

Set `HARNESS_LIVE_API=1` only for a test that really calls a model.
These demos do not.

## Listings

| File | What it shows |
| --- | --- |
| `listings/08-03-claude-tool-choice.py` | A booking tool and allowed_tools |
| `listings/08-03-langchain-tool-choice.py` | Middleware that keeps book_flight |
| `listings/08-04-semantic-validator.py` | Price, date, and return-date checks |
| `listings/08-05-claude-policy.py` | Budget ceiling and a denied tool |
| `listings/08-05-langchain-policy-middleware.py` | Model and tool call limits |
| `listings/08-06-claude-prehook.py` | Refund cap before the tool runs |
| `listings/08-06-langchain-prehook.py` | The same cap as middleware |
| `listings/08-07-claude-posthook.py` | Mask a card number and an SSN |
| `listings/08-07-date-normalize.py` | US dates to ISO-8601 |
| `listings/08-07-langchain-posthook.py` | Mask identifiers after the tool |
| `listings/08-08-validation-retry.py` | Retry, then a fallback model |
| `listings/08-10-claude-integrated.py` | Hooks plus schema validation |
| `listings/08-10-langchain-integrated.py` | Budgets, refund cap, and masking |
