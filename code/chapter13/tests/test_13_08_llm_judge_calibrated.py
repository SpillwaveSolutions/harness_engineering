"""Tests for listing 13-08-llm-judge-calibrated (§13.8).

Verifies that score_booking_response:
  - exists and is callable
  - uses the 'claude-sonnet-4-6' model name
  - sets the four gen_ai.evaluation.* span attributes
  - returns a dict with score, label, explanation keys

The Anthropic client is mocked so no live API call occurs.
The tracer span is mocked so no OTLP exporter is needed.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_judge_module():
    """Load 13-08-llm-judge-calibrated.py with Anthropic client patched."""
    anthropic_mock = MagicMock()
    with patch.dict(sys.modules, {"anthropic": anthropic_mock}):
        path = LISTINGS_DIR / "13-08-llm-judge-calibrated.py"
        if not path.exists():
            pytest.fail(f"listing not found at {path}")
        spec = importlib.util.spec_from_file_location("listing_13_08", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_13_08"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod, anthropic_mock


def test_score_booking_response_is_callable():
    """§13.8: score_booking_response must be defined and callable."""
    mod, _ = _load_judge_module()
    assert callable(mod.score_booking_response)


def test_booking_quality_rubric_is_non_empty():
    """§13.8: BOOKING_QUALITY_RUBRIC must be a non-empty string."""
    mod, _ = _load_judge_module()
    assert isinstance(mod.BOOKING_QUALITY_RUBRIC, str)
    assert len(mod.BOOKING_QUALITY_RUBRIC) > 50, (
        "BOOKING_QUALITY_RUBRIC should contain a meaningful rubric"
    )


def test_score_booking_response_model_name():
    """§13.8: model name used in the judge call must be 'claude-sonnet-4-6'."""
    import inspect
    mod, _ = _load_judge_module()
    src = inspect.getsource(mod.score_booking_response)
    assert "claude-sonnet-4-6" in src


def test_score_booking_response_sets_span_attributes(load_listing):
    """§13.8: sets gen_ai.evaluation.name, score.value, score.label, explanation on span."""
    # Use a different loading path that goes through load_listing fixture
    # (which also patches at module level)
    anthropic_mock = MagicMock()
    with patch.dict(sys.modules, {"anthropic": anthropic_mock}):
        path = LISTINGS_DIR / "13-08-llm-judge-calibrated.py"
        if not path.exists():
            pytest.fail("listing not found")
        spec = importlib.util.spec_from_file_location("listing_13_08_b", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_13_08_b"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    # Mock the tracer to capture span attribute calls
    span_mock = MagicMock()
    span_mock.__enter__ = lambda s: span_mock
    span_mock.__exit__ = MagicMock(return_value=False)
    tracer_mock = MagicMock()
    tracer_mock.start_as_current_span.return_value = span_mock
    mod.tracer = tracer_mock

    # The listing does not construct a network client at import.
    verdict_dict = {"score": 4, "label": "PASS", "explanation": "Booking is valid."}
    judge_response = MagicMock()
    judge_response.content = [MagicMock(text=json.dumps(verdict_dict))]
    mod.client = MagicMock()
    mod.client.messages.create.return_value = judge_response

    # Inject parse_verdict so it works without its own dependency
    def parse_verdict(text: str) -> dict:
        return json.loads(text)

    mod.parse_verdict = parse_verdict

    result = mod.score_booking_response(
        booking_response="Booked flight AA101 for John Doe, economy, 2026-06-15.",
        passenger_constraints={"name": "John Doe", "seat_class": "economy"},
    )

    assert result["score"] == 4
    assert result["label"] == "PASS"

    attr_calls = {c.args[0]: c.args[1] for c in span_mock.set_attribute.call_args_list}
    assert attr_calls.get("gen_ai.evaluation.name") == "booking_quality"
    assert attr_calls.get("gen_ai.evaluation.score.value") == 4
    assert attr_calls.get("gen_ai.evaluation.score.label") == "PASS"
    assert "gen_ai.evaluation.explanation" in attr_calls
