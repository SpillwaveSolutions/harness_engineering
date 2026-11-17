# Chapter 11 listings

Licensed under the MIT license in `code/LICENSE` (Copyright (c) 2026 Spillwave Solutions).

Generator, critic, and human-approval listings for the travel-booking
agent. The modules are stdlib only. Importing them does not read the
environment or open a network connection.

| File | What it does |
| --- | --- |
| `listings/11-02-contracts.py` | `ProposedAction`, `CritiqueResult`, and `ArbitrationDecision`. |
| `listings/11-03-critic-prompt.py` | `CRITIC_SYSTEM_PROMPT` for the adversarial critic. |
| `listings/11-05-escalation-policy.py` | `EscalationPolicy.decide()` routes proceed, amend, escalate, or default_deny. |
| `listings/11-06-approval-gate.py` | `request_human_approval()` notifies, polls, and times out. |
| `listings/11-06-interrupt-config.py` | Interrupt map: a dict for `book_flight`, `False` for `search_flights`. |

## Setup

```bash
cd code/chapter11
uv sync --all-groups
```

## Run offline

```bash
uv run python listings/11-05-escalation-policy.py
```

Expected offline output:

```text
escalate
```

That run asks `decide()` about irreversible `book_flight` with the
confidence floor met. The other listings are libraries; exercise them
through pytest.

## Tests

```bash
uv run pytest -q
```

Tests call `decide()`, `request_human_approval()`, and the contract
constructors and assert the results. Nothing is skipped for a missing
import.

## Live calls

These listings do not call a model API. `HARNESS_LIVE_API=1` does not
change their behavior.
