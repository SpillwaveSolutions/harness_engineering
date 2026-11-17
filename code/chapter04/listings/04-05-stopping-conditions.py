"""Listing 04-05: The four stopping conditions every production loop needs.

Implements the two-layer stopping architecture described in Section 4.5:

  Layer 1 -- continuation signal (data plane output, handled by caller).
  Layer 2 -- four control-plane policy checks implemented here.

The parameter is named ``token_budget`` (not ``max_tokens``) to avoid
shadowing the Anthropic API per-call parameter of the same name.

Chapter 4, Section 4.5 -- The four stopping conditions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Harness state -- accumulates across loop iterations.
# ---------------------------------------------------------------------------

@dataclass
class HarnessState:
    """Mutable state accumulated by the harness across loop turns.

    Attributes:
        turns: Number of completed loop iterations.
        total_tokens: Cumulative token count across all model calls.
        tool_call_hashes: SHA-256 hashes of each turn's tool-call batch,
            oldest first. Used by the no-progress detector.
    """

    turns: int = 0
    total_tokens: int = 0
    tool_call_hashes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The four stopping conditions (matches the prose representative block).
# ---------------------------------------------------------------------------

def check_stopping_conditions(  # ①
    state: HarnessState,
    tool_calls: list[dict],
    *,
    max_turns: int = 20,
    token_budget: int = 100_000,  # renamed from max_tokens to avoid
    # shadowing the Anthropic API per-call parameter
    no_progress_window: int = 3,
) -> str | None:
    """Return a stop-reason string when a condition fires, or None to continue.

    Conditions are checked in priority order. The caller should treat a
    non-None return as a signal to halt or escalate rather than looping.

    Args:
        state: Accumulated harness state (mutated in place for Condition 3).
        tool_calls: Tool-call batch from the current turn (may be empty).
        max_turns: Hard upper bound on loop iterations (Condition 1).
        token_budget: Cumulative token ceiling across all turns (Condition 2).
        no_progress_window: Number of identical consecutive tool-call batches
            that trigger the no-progress halt (Condition 3).

    Returns:
        ``"max_turns"`` | ``"token_budget"`` | ``"no_progress"`` | ``None``
    """
    # Condition 1: maximum turns ②
    if state.turns >= max_turns:
        return "max_turns"

    # Condition 2: token budget ③
    if state.total_tokens >= token_budget:
        return "token_budget"

    # Condition 3: no-progress detection ④
    if tool_calls:
        call_hash = hashlib.sha256(
            json.dumps(tool_calls, sort_keys=True).encode()
        ).hexdigest()
        state.tool_call_hashes.append(call_hash)
        recent = state.tool_call_hashes[-no_progress_window:]
        if (
            len(recent) == no_progress_window
            and len(set(recent)) == 1
        ):
            return "no_progress"

    # Condition 4: goal-achievement check runs as a separate evaluator step
    # (see Chapter 14 for the full evaluator-optimizer pattern) ⑤
    return None  # continue


# ---------------------------------------------------------------------------
# Annotations (load-bearing lines)
# ---------------------------------------------------------------------------
# ① Function signature: state is mutated by the no-progress tracker, so it
#   is the caller's responsibility to pass the same HarnessState object on
#   every iteration.
# ② Condition 1 (max_turns): checked first because it is the cheapest test
#   and the most universal harness-level backstop.
# ③ Condition 2 (token_budget): uses a whole-run cumulative total, not the
#   per-call max_tokens parameter, so it bounds session-level spend.
# ④ Condition 3 (no_progress): hashes the tool-call batch; identical hashes
#   for no_progress_window consecutive turns indicate a stuck loop.
# ⑤ Condition 4 (goal-achievement): deferred to Chapter 14's
#   evaluator-optimizer pattern; included here as an explicit placeholder so
#   the architecture is visible even before the implementation exists.


def main() -> None:
    state = HarnessState()
    same_call = [{"name": "search", "input": {"query": "best practices"}}]

    for i in range(4):
        state.turns = i
        result = check_stopping_conditions(
            state, same_call, max_turns=20, token_budget=100_000
        )
        print(f"Turn {i}: {result}")


if __name__ == "__main__":
    main()
