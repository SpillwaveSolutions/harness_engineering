"""Tests for listing 11-02-contracts.

Three pure dataclasses with no external dependencies. Load-bearing
claims from §11.2:
1. `ProposedAction` carries tool name, input dict, and generator
   rationale.
2. `CritiqueResult.confidence_floor_met` is a precomputed boolean
   (True when `confidence_score >= 0.65` is the convention; the field
   itself is just a bool).
3. `ArbitrationDecision.decision` is one of four literal values:
   "proceed", "amend", "escalate", "default_deny".
4. `ArbitrationDecision.amended_input` is None when the arbiter did
   not modify the plan.
"""

from __future__ import annotations

import dataclasses

import pytest


@pytest.fixture
def contracts(load_listing):
    return load_listing("11-02-contracts")


def test_proposed_action_has_required_fields(contracts):
    action = contracts.ProposedAction(
        tool_name="book_flight",
        tool_input={"fare_id": "abc"},
        generator_rationale="found a flexible fare",
    )
    assert action.tool_name == "book_flight"
    assert action.tool_input == {"fare_id": "abc"}
    assert action.generator_rationale == "found a flexible fare"


def test_proposed_action_is_dataclass(contracts):
    assert dataclasses.is_dataclass(contracts.ProposedAction)


def test_critique_result_floor_is_bool(contracts):
    critique = contracts.CritiqueResult(
        objection="business class violates economy constraint",
        confidence_floor_met=False,
        confidence_score=0.12,
        rubric_scores={"price_constraint_met": 0.0},
    )
    assert critique.confidence_floor_met is False
    assert isinstance(critique.confidence_floor_met, bool)


def test_arbitration_decision_amended_input_none_by_default(contracts):
    decision = contracts.ArbitrationDecision(
        decision="proceed",
        rationale="reversible action, agreement",
        amended_input=None,
    )
    assert decision.amended_input is None
    assert decision.decision == "proceed"


def test_arbitration_decision_amended_input_when_amend(contracts):
    decision = contracts.ArbitrationDecision(
        decision="amend",
        rationale="critic suggested economy class",
        amended_input={"cabin": "economy"},
    )
    assert decision.amended_input == {"cabin": "economy"}


def test_arbitration_decision_accepts_all_four_literals(contracts):
    for value in ("proceed", "amend", "escalate", "default_deny"):
        decision = contracts.ArbitrationDecision(
            decision=value,
            rationale="exercise the literal",
            amended_input=None,
        )
        assert decision.decision == value
