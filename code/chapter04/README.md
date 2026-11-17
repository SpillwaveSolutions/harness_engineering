# Chapter 4 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

The harness split into a control plane and a data plane, the seven components, the control loop, the continuation signal, the stopping conditions, and one travel harness wired through the agent SDK.

- `listings/04-01-two-plane-sketch.py` runs a goal through the control plane. The data plane returns an offline reply.
- `listings/04-02-harness-components.py` is the seven-field checklist.
- `listings/04-03-control-loop.py` walks `end_turn` on a fake client.
- `listings/04-04-continuation-signal.py` maps `stop_reason` to a return value or an error.
- `listings/04-05-stopping-conditions.py` shows the no-progress stop after three identical tool batches.
- `listings/04-09-harness-iteration.py` imports `ClaudeAgentOptions`, `HookMatcher`, and `query`. Offline, it does not call `query`.

## Setup

```bash
cd code/chapter04 && uv sync --all-groups
```

## Run

```bash
uv run python listings/04-01-two-plane-sketch.py
```

```
offline reply: Book a flight to Tokyo.
```

```bash
uv run python listings/04-02-harness-components.py
```

```
context_manager, memory, validators, tools, observability, recovery, coordination
spans
```

```bash
uv run python listings/04-03-control-loop.py
```

```
Loop result: Hello from the loop.
```

```bash
uv run python listings/04-04-continuation-signal.py
```

```
end_turn result: The answer is 42.
tool_use result: continue
```

```bash
uv run python listings/04-05-stopping-conditions.py
```

```
Turn 0: None
Turn 1: None
Turn 2: no_progress
Turn 3: no_progress
```

```bash
uv run python listings/04-09-harness-iteration.py
```

stdout:

```
Stub result for: Book a flight to Tokyo.
```

stderr:

```
offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY to run a live harness query.
```

## Live calls

`run_travel_harness` calls `query` only when `HARNESS_LIVE_API=1` and `ANTHROPIC_API_KEY` are both set. Otherwise it returns `Stub result for:` plus the user request and does not touch the network.
