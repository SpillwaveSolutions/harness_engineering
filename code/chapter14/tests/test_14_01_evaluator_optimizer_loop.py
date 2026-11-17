"""Tests for listing 14-01-evaluator-optimizer-loop (§14.2).

Verifies:
  - Module imports without NameError (JUDGE_SYSTEM_PROMPT, generate_booking_response,
    assemble_feedback all defined).
  - run_evaluator_optimizer returns budget_exceeded when cost limit hit.
  - run_evaluator_optimizer returns pass when evaluator returns PASS.
  - run_evaluator_optimizer returns max_iterations after exhausting loop.
  - evaluate_booking_response is callable.
  - generate_booking_response accepts optional feedback kwarg.
  - assemble_feedback returns a non-empty string.

Tests patch the Anthropic client to avoid live network calls.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    """Load 14-01 with anthropic client patched out."""
    mock_anthropic = MagicMock()
    path = LISTINGS_DIR / "14-01-evaluator-optimizer-loop.py"
    with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
        spec = importlib.util.spec_from_file_location(
            "listing_14_01", path
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_14_01"] = mod
        spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_imports_without_nameerror():
    """§14.2: module must define JUDGE_SYSTEM_PROMPT, generate_booking_response,
    assemble_feedback without NameError."""
    mod = _load_module()
    assert hasattr(mod, "JUDGE_SYSTEM_PROMPT"), (
        "JUDGE_SYSTEM_PROMPT must be defined"
    )
    assert hasattr(mod, "generate_booking_response"), (
        "generate_booking_response must be defined"
    )
    assert hasattr(mod, "assemble_feedback"), (
        "assemble_feedback must be defined"
    )
    assert hasattr(mod, "run_evaluator_optimizer"), (
        "run_evaluator_optimizer must be defined"
    )


def test_judge_system_prompt_is_string():
    """§14.2: JUDGE_SYSTEM_PROMPT must be a non-empty string."""
    mod = _load_module()
    assert isinstance(mod.JUDGE_SYSTEM_PROMPT, str)
    assert len(mod.JUDGE_SYSTEM_PROMPT.strip()) > 0


def test_generate_booking_response_accepts_feedback():
    """§14.2: generate_booking_response must accept optional feedback kwarg."""
    mod = _load_module()
    result = mod.generate_booking_response(
        "Book a flight to Paris", feedback="Try again"
    )
    assert isinstance(result, str)


def test_assemble_feedback_returns_nonempty_string():
    """§14.2: assemble_feedback must return a non-empty string."""
    mod = _load_module()
    verdict = {
        "label": "FAIL",
        "explanation": "Flight ID missing.",
        "cost_usd": 0.01,
    }
    feedback = mod.assemble_feedback(verdict)
    assert isinstance(feedback, str)
    assert len(feedback) > 0


def test_run_evaluator_optimizer_returns_budget_exceeded():
    """§14.2: budget_exceeded returned when cost exceeds max_budget_usd."""
    mod = _load_module()

    # Patch evaluate_booking_response to always return expensive verdict.
    expensive_verdict = {
        "label": "FAIL",
        "explanation": "stub fail",
        "cost_usd": 1.00,  # each call costs $1 — blows the 0.50 limit
    }
    mod.evaluate_booking_response = MagicMock(
        return_value=expensive_verdict
    )

    result = mod.run_evaluator_optimizer(
        "Book flight to Paris",
        max_iterations=3,
        max_budget_usd=0.50,
    )
    assert result["status"] == "budget_exceeded"


def test_run_evaluator_optimizer_returns_pass():
    """§14.2: pass returned when evaluator returns PASS on first attempt."""
    mod = _load_module()

    pass_verdict = {
        "label": "PASS",
        "explanation": "",
        "cost_usd": 0.01,
    }
    mod.evaluate_booking_response = MagicMock(
        return_value=pass_verdict
    )

    result = mod.run_evaluator_optimizer(
        "Book flight to London",
        max_iterations=3,
        max_budget_usd=0.50,
    )
    assert result["status"] == "pass"
    assert result["iterations"] == 0


def test_run_evaluator_optimizer_max_iterations():
    """§14.2: max_iterations returned after exhausting the loop."""
    mod = _load_module()

    fail_verdict = {
        "label": "FAIL",
        "explanation": "always fail",
        "cost_usd": 0.01,
    }
    mod.evaluate_booking_response = MagicMock(
        return_value=fail_verdict
    )

    result = mod.run_evaluator_optimizer(
        "Book flight to Tokyo",
        max_iterations=2,
        max_budget_usd=10.0,
    )
    assert result["status"] == "max_iterations"


def test_evaluate_booking_response_offline(monkeypatch):
    """Missing live flag returns a deterministic verdict and does not call out."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_module()
    mod.client = None
    verdict = mod.evaluate_booking_response("Booked flight AA100")
    assert verdict["status"] == "offline"
    assert verdict["label"] == "NEEDS_REVIEW"
    assert verdict["cost_usd"] == 0.0
