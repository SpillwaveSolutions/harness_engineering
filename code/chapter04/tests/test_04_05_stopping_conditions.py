"""Tests for listing 04-05-stopping-conditions.

Exercises check_stopping_conditions for each of the three computable
stopping conditions (max_turns, token_budget, no_progress) plus the
continuation case (None).
"""

from __future__ import annotations


def test_max_turns_fires_when_turns_at_limit(load_listing) -> None:
    """Condition 1 fires when state.turns >= max_turns."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState(turns=20)
    result = m.check_stopping_conditions(
        state, [], max_turns=20, token_budget=100_000
    )
    assert result == "max_turns"


def test_max_turns_does_not_fire_before_limit(load_listing) -> None:
    """Condition 1 does not fire when turns is below max_turns."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState(turns=5)
    result = m.check_stopping_conditions(
        state, [], max_turns=20, token_budget=100_000
    )
    assert result is None


def test_token_budget_fires_when_at_limit(load_listing) -> None:
    """Condition 2 fires when total_tokens >= token_budget."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState(turns=0, total_tokens=100_000)
    result = m.check_stopping_conditions(
        state, [], max_turns=20, token_budget=100_000
    )
    assert result == "token_budget"


def test_token_budget_does_not_fire_below_limit(load_listing) -> None:
    """Condition 2 does not fire when tokens are under budget."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState(turns=0, total_tokens=50_000)
    result = m.check_stopping_conditions(
        state, [], max_turns=20, token_budget=100_000
    )
    assert result is None


def test_no_progress_fires_after_window_of_identical_calls(
    load_listing,
) -> None:
    """Condition 3 fires when the same tool-call batch repeats no_progress_window times."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState()
    same_call = [{"name": "search", "input": {"query": "python"}}]

    # First two calls should not fire.
    for _ in range(2):
        result = m.check_stopping_conditions(
            state,
            same_call,
            max_turns=20,
            token_budget=100_000,
            no_progress_window=3,
        )
        assert result is None, "Should not fire before window is full"

    # Third identical call completes the window and fires no_progress.
    result = m.check_stopping_conditions(
        state,
        same_call,
        max_turns=20,
        token_budget=100_000,
        no_progress_window=3,
    )
    assert result == "no_progress"


def test_no_progress_resets_on_different_call(load_listing) -> None:
    """Condition 3 does not fire when the tool-call batch changes."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState()
    call_a = [{"name": "search", "input": {"query": "alpha"}}]
    call_b = [{"name": "search", "input": {"query": "beta"}}]

    m.check_stopping_conditions(state, call_a, max_turns=20)
    m.check_stopping_conditions(state, call_b, max_turns=20)
    result = m.check_stopping_conditions(state, call_a, max_turns=20)
    assert result is None


def test_continuation_when_no_condition_fires(load_listing) -> None:
    """Returns None (continue) when state is healthy and no tools repeat."""
    m = load_listing("04-05-stopping-conditions")
    state = m.HarnessState(turns=0, total_tokens=0)
    result = m.check_stopping_conditions(
        state,
        [{"name": "echo", "input": {"msg": "ping"}}],
        max_turns=20,
        token_budget=100_000,
    )
    assert result is None
