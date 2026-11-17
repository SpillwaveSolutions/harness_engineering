# Chapter 12 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Agent-to-agent coordination listings for the travel-booking harness.
Importing a listing does not open a socket, read `sys.argv`, or require
an API key. Functions that would talk to Kafka, a partner agent, or a
model return a deterministic offline dict or list instead.

| File | What it does |
| --- | --- |
| `listings/12-04-task-state.py` | Eight-value `TaskState` enum. Wire values for input and auth use hyphens. |
| `listings/12-05-message-parts.py` | `build_loyalty_request()` builds a `Message` with text, file, and data parts. |
| `listings/12-06-sse-consumer.py` | `stream_loyalty_task()` raises `InputRequired`, `AuthRequired`, or `TaskFailed`. |
| `listings/12-08-hub-and-spoke.py` | `TravelCoordinator.handle_request()` fans out to two spokes and merges them. |
| `listings/12-11-hybrid-agent.py` | `create_hybrid_server()` mounts MCP at `/mcp` and A2A routes at `/a2a`. |
| `listings/12-12-kafka-consumer.py` | `run_loyalty_consumer()` stays offline unless `HARNESS_LIVE_API=1`. |
| `listings/12-13-provenance.py` | Pydantic claim, artifact, and synthesis models. |
| `listings/12-14-a2a-sdk-server.py` | `HotelLoyaltyExecutor` and `build_card()`. |
| `listings/12-14-adk-server.py` | `create_adk_a2a_server()` builds a FastAPI app. It is not called at import. |
| `listings/12-15-harness-integration.py` | `TravelBookingHarness.book_travel()` discovers a local card and returns offline artifacts. |

## Setup

```bash
cd code/chapter12
uv sync --all-groups
```

## Run offline

```bash
uv run python listings/12-05-message-parts.py
uv run python listings/12-08-hub-and-spoke.py
uv run python listings/12-12-kafka-consumer.py
uv run python listings/12-15-harness-integration.py
```

Expected offline output includes:

```text
{"message_id": "loyalty-ACC123", "parts": 3, "text": "Check loyalty status for account ACC123"}
{"request": "SFO next week", "status": "ok", "spokes": [{"name": "flight-search", ...}, {"name": "hotel-loyalty", ...}]}
[{"topic": "hotel-loyalty-requests", "status": "offline", "parts": 1, ...}]
{"flights": {"request": "book a hotel", "options": []}, "loyalty": {"accountId": "ACC123456", "status": "offline"}, ...}
```

Stderr explains the missing key or the skipped broker connection.
`12-11` prints `{'account_id': 'ACC123', 'points': 0, 'tier': 'unknown', 'status': 'offline'}`.

## Tests

```bash
uv run pytest -q
```

Tests call the functions above and assert the offline results. They do
not skip on import errors.

## Live calls

Set `HARNESS_LIVE_API=1` before `run_loyalty_consumer()` or
`_discover_loyalty_agent()` to take the network branch. Model calls
also need `ANTHROPIC_API_KEY`. The default test run leaves both unset.
