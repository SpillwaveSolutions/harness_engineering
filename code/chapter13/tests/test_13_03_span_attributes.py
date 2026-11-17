"""Tests for listing 13-03-span-attributes (§13.3).

Verifies that record_cost computes harness.usage.cost_usd correctly from
token counts and the MODEL_PRICING table, and that record_eval_verdict
sets the four gen_ai.evaluation.* attributes with the truncation discipline
on explanation.
"""

from __future__ import annotations

from unittest.mock import MagicMock


def test_record_cost_computes_cost_usd_correctly(load_listing):
    """§13.3: record_cost applies MODEL_PRICING to produce harness.usage.cost_usd."""
    listing = load_listing("13-03-span-attributes")

    span = MagicMock()
    # claude-sonnet-4-6: $3.00/M input, $15.00/M output
    listing.record_cost(span, "claude-sonnet-4-6", input_tokens=1_000_000, output_tokens=1_000_000)

    calls = {call.args[0]: call.args[1] for call in span.set_attribute.call_args_list}
    assert calls["gen_ai.usage.input_tokens"] == 1_000_000
    assert calls["gen_ai.usage.output_tokens"] == 1_000_000
    # 1M input × $3.00/M + 1M output × $15.00/M = $18.00
    assert abs(calls["harness.usage.cost_usd"] - 18.00) < 1e-6


def test_record_cost_unknown_model_uses_zero_rate(load_listing):
    """§13.3: an unknown model falls back to zero cost rather than raising."""
    listing = load_listing("13-03-span-attributes")

    span = MagicMock()
    listing.record_cost(span, "unknown-model-xyz", input_tokens=500, output_tokens=200)

    calls = {call.args[0]: call.args[1] for call in span.set_attribute.call_args_list}
    assert calls["harness.usage.cost_usd"] == 0.0


def test_record_cost_fractional_tokens(load_listing):
    """§13.3: record_cost handles small token counts correctly (sub-cent cost)."""
    listing = load_listing("13-03-span-attributes")

    span = MagicMock()
    # 1000 input tokens × $3/M = $0.000003
    listing.record_cost(span, "claude-sonnet-4-6", input_tokens=1_000, output_tokens=0)

    calls = {call.args[0]: call.args[1] for call in span.set_attribute.call_args_list}
    assert abs(calls["harness.usage.cost_usd"] - 0.003) < 1e-9


def test_record_eval_verdict_sets_all_four_attributes(load_listing):
    """§13.3: record_eval_verdict sets name, score.value, score.label, explanation."""
    listing = load_listing("13-03-span-attributes")

    span = MagicMock()
    listing.record_eval_verdict(
        span,
        name="booking_quality",
        score=4.5,
        label="PASS",
        explanation="Flight ID valid, constraints matched.",
    )

    calls = {call.args[0]: call.args[1] for call in span.set_attribute.call_args_list}
    assert calls["gen_ai.evaluation.name"] == "booking_quality"
    assert calls["gen_ai.evaluation.score.value"] == 4.5
    assert calls["gen_ai.evaluation.score.label"] == "PASS"
    assert calls["gen_ai.evaluation.explanation"] == "Flight ID valid, constraints matched."


def test_record_eval_verdict_truncates_explanation_to_500(load_listing):
    """§13.3: explanation is truncated to 500 chars to guard against PII leakage."""
    listing = load_listing("13-03-span-attributes")

    span = MagicMock()
    long_explanation = "x" * 1000
    listing.record_eval_verdict(span, name="q", score=3.0, label="NEEDS_REVIEW", explanation=long_explanation)

    calls = {call.args[0]: call.args[1] for call in span.set_attribute.call_args_list}
    assert len(calls["gen_ai.evaluation.explanation"]) == 500
