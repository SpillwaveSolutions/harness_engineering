"""Tests for listing 11-03-critic-prompt.

The listing is a single named constant `CRITIC_SYSTEM_PROMPT` carrying
the adversarial system prompt for the travel-booking critic. The
load-bearing claims from §11.3 are structural rather than behavioral:

1. The prompt contains the adversarial framing line ("find the
   strongest possible objection") — Mitigation One.
2. The prompt contains the four-criterion rubric — Mitigation Four.
3. The prompt requests a JSON object with the four required output
   fields, including `confidence_floor_met` keyed to the 0.65 floor.
4. The prompt contains the anti-hedge clause ("Do NOT explain why the
   plan might be acceptable") — counter-sycophancy.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def critic_prompt_module(load_listing):
    return load_listing("11-03-critic-prompt")


def test_prompt_constant_exported(critic_prompt_module):
    assert hasattr(critic_prompt_module, "CRITIC_SYSTEM_PROMPT")
    assert isinstance(
        critic_prompt_module.CRITIC_SYSTEM_PROMPT, str
    )


def test_prompt_contains_adversarial_framing(critic_prompt_module):
    prompt = critic_prompt_module.CRITIC_SYSTEM_PROMPT
    assert "strongest possible objection" in prompt
    assert "Do not look for reasons the plan is good" in prompt


def test_prompt_contains_full_rubric(critic_prompt_module):
    prompt = critic_prompt_module.CRITIC_SYSTEM_PROMPT
    for criterion in (
        "price_constraint_met",
        "cabin_class_correct",
        "date_flexibility_preserved",
        "refundability_matches_risk",
    ):
        assert criterion in prompt, (
            f"rubric criterion {criterion!r} missing from prompt"
        )


def test_prompt_requires_confidence_floor_at_065(critic_prompt_module):
    prompt = critic_prompt_module.CRITIC_SYSTEM_PROMPT
    assert "confidence_floor_met" in prompt
    assert "0.65" in prompt


def test_prompt_has_anti_hedge_clause(critic_prompt_module):
    prompt = critic_prompt_module.CRITIC_SYSTEM_PROMPT
    assert "Do NOT explain why the plan might be acceptable" in prompt
    assert "Do NOT hedge" in prompt
