"""Tests for listing 11-05-escalation-policy.

The listing references `ProposedAction` and `CritiqueResult` defined in
listing 11-02-contracts. Because the prose listing carries
`from __future__ import annotations`, the references are strings at
import time, and the listing imports cleanly. To exercise `decide()` at
runtime, we load the contracts module first and pass real instances of
the dataclasses.

Load-bearing claims from §11.5:
1. Irreversible tool + confidence_floor_met=False → "default_deny".
2. Irreversible tool + confidence_floor_met=True → "escalate".
3. Reversible tool + confidence_floor_met=False → "escalate".
4. Reversible tool + large delta + rounds remaining → "amend".
5. Reversible tool + small delta or rounds exhausted → "proceed".
6. The `irreversible_tools` set is a harness-side registry (not a
   model decision); the model cannot talk the arbiter out of escalating
   a tool listed there.
7. `decide()` is deterministic: same inputs yield the same routing.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def contracts(load_listing):
    return load_listing("11-02-contracts")


@pytest.fixture
def policy_module(load_listing, contracts):
    """Load 11-05-escalation-policy.

    Because the listing has `from __future__ import annotations`, type
    references in `decide()` are deferred strings and the listing
    imports cleanly. We do not need to inject contracts into globals at
    import time; we just pass real dataclass instances when calling
    `decide()`.
    """
    return load_listing("11-05-escalation-policy")


@pytest.fixture
def policy(policy_module):
    return policy_module.EscalationPolicy(
        irreversible_tools={"book_flight", "cancel_booking"},
    )


@pytest.fixture
def make_proposed(contracts):
    def _make(tool_name: str) -> object:
        return contracts.ProposedAction(
            tool_name=tool_name,
            tool_input={"fare_id": "x"},
            generator_rationale="exercise the policy",
        )

    return _make


@pytest.fixture
def make_critique(contracts):
    def _make(
        confidence_score: float,
        confidence_floor_met: bool | None = None,
    ) -> object:
        return contracts.CritiqueResult(
            objection="test objection",
            confidence_floor_met=(
                confidence_floor_met
                if confidence_floor_met is not None
                else confidence_score >= 0.65
            ),
            confidence_score=confidence_score,
            rubric_scores={},
        )

    return _make


def test_irreversible_below_floor_returns_default_deny(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("book_flight")
    critique = make_critique(confidence_score=0.40)
    assert policy.decide(proposed, critique, round_number=0) == (
        "default_deny"
    )


def test_irreversible_above_floor_returns_escalate(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("book_flight")
    critique = make_critique(confidence_score=0.90)
    assert policy.decide(proposed, critique, round_number=0) == (
        "escalate"
    )


def test_reversible_below_floor_returns_escalate(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("search_flights")
    critique = make_critique(confidence_score=0.40)
    assert policy.decide(proposed, critique, round_number=0) == (
        "escalate"
    )


def test_reversible_high_confidence_returns_proceed(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("search_flights")
    critique = make_critique(confidence_score=0.95)
    assert policy.decide(proposed, critique, round_number=0) == (
        "proceed"
    )


def test_reversible_large_delta_with_rounds_returns_amend(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("search_flights")
    # delta = 1.0 - 0.70 = 0.30, above CONFIDENCE_DELTA_THRESHOLD=0.20
    critique = make_critique(confidence_score=0.70)
    assert policy.decide(proposed, critique, round_number=0) == (
        "amend"
    )


def test_reversible_large_delta_but_rounds_exhausted_returns_proceed(
    policy, make_proposed, make_critique, policy_module,
):
    proposed = make_proposed("search_flights")
    critique = make_critique(confidence_score=0.70)
    rounds = policy_module.MAX_AMEND_ROUNDS
    assert policy.decide(proposed, critique, round_number=rounds) == (
        "proceed"
    )


def test_decide_is_deterministic(
    policy, make_proposed, make_critique,
):
    proposed = make_proposed("book_flight")
    critique = make_critique(confidence_score=0.95)
    first = policy.decide(proposed, critique, round_number=0)
    second = policy.decide(proposed, critique, round_number=0)
    third = policy.decide(proposed, critique, round_number=0)
    assert first == second == third == "escalate"


def test_irreversible_registry_is_harness_side(
    policy_module, make_proposed, make_critique,
):
    """Same proposal evaluated against two policies with different
    `irreversible_tools` sets routes differently. The registry is the
    arbiter's source of truth, not the model's confidence score."""
    strict = policy_module.EscalationPolicy(
        irreversible_tools={"book_flight"},
    )
    permissive = policy_module.EscalationPolicy(
        irreversible_tools=set(),
    )
    proposed = make_proposed("book_flight")
    critique = make_critique(confidence_score=0.95)

    assert strict.decide(proposed, critique, round_number=0) == (
        "escalate"
    )
    assert permissive.decide(proposed, critique, round_number=0) == (
        "proceed"
    )


def test_local_dataclasses_irreversible_tool(policy_module):
    """decide() on an irreversible tool returns escalate or default_deny."""
    proposed = policy_module.ProposedAction(tool_name="book_flight")
    above = policy_module.CritiqueResult(
        tool_name="book_flight",
        confidence_floor_met=True,
        confidence_score=0.9,
    )
    below = policy_module.CritiqueResult(
        tool_name="book_flight",
        confidence_floor_met=False,
        confidence_score=0.2,
    )
    policy = policy_module.EscalationPolicy(
        irreversible_tools={"book_flight"},
    )
    high = policy.decide(proposed, above, round_number=0)
    low = policy.decide(proposed, below, round_number=0)
    assert high in {"escalate", "default_deny"}
    assert low in {"escalate", "default_deny"}
    assert high == "escalate"
    assert low == "default_deny"


def test_confidence_floor_constant_is_065(policy_module):
    assert policy_module.CONFIDENCE_FLOOR == 0.65


def test_max_amend_rounds_constant_is_2(policy_module):
    assert policy_module.MAX_AMEND_ROUNDS == 2
