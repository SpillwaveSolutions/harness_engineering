"""Tests for listing 14-02-llm-judge-rubric (§14.3).

Verifies:
  - JUDGE_SYSTEM_PROMPT is a non-empty string.
  - Rubric text contains all four scoring fields.
  - PASS/NEEDS_REVIEW/FAIL labels are named in the prompt.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "14-02-llm-judge-rubric.py"
    spec = importlib.util.spec_from_file_location("listing_14_02", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_02"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_judge_system_prompt_defined():
    """§14.3: JUDGE_SYSTEM_PROMPT must be defined and non-empty."""
    mod = _load_module()
    assert hasattr(mod, "JUDGE_SYSTEM_PROMPT")
    assert isinstance(mod.JUDGE_SYSTEM_PROMPT, str)
    assert len(mod.JUDGE_SYSTEM_PROMPT.strip()) > 0


def test_rubric_contains_four_fields():
    """§14.3: rubric must score flight_id_valid, passenger_constraints_met,
    booking_status_confirmed, and no_hallucinated_details."""
    mod = _load_module()
    prompt = mod.JUDGE_SYSTEM_PROMPT
    for field in [
        "flight_id_valid",
        "passenger_constraints_met",
        "booking_status_confirmed",
        "no_hallucinated_details",
    ]:
        assert field in prompt, (
            f"Rubric must contain field '{field}'"
        )


def test_rubric_contains_verdict_labels():
    """§14.3: rubric must name PASS, NEEDS_REVIEW, FAIL verdict labels."""
    mod = _load_module()
    prompt = mod.JUDGE_SYSTEM_PROMPT
    for label in ["PASS", "NEEDS_REVIEW", "FAIL"]:
        assert label in prompt, (
            f"Rubric must contain verdict label '{label}'"
        )
