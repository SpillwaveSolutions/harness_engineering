"""Tests for listing 14-07-promotion-gate (§14.11).

Verifies:
  - Module imports without NameError (thresholds and cost_thresholds defined).
  - GateResult dataclass is importable.
  - run_promotion_gate passes when all four lanes pass.
  - run_promotion_gate blocks when quality is below floor.
  - run_promotion_gate blocks when regression exceeds max_regression.
  - run_promotion_gate blocks when a safety check fails.
  - run_promotion_gate blocks when cost exceeds ceiling.
  - thresholds covers booking_quality with min and max_regression keys.
  - cost_thresholds covers cost_usd_per_session.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "14-07-promotion-gate.py"
    spec = importlib.util.spec_from_file_location(
        "listing_14_07", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_07"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_imports_without_nameerror():
    """§14.11: thresholds and cost_thresholds must be defined."""
    mod = _load_module()
    assert hasattr(mod, "thresholds"), "thresholds must be defined"
    assert hasattr(mod, "cost_thresholds"), (
        "cost_thresholds must be defined"
    )


def test_thresholds_has_booking_quality():
    """§14.11: thresholds must cover booking_quality with min+max_regression."""
    mod = _load_module()
    assert "booking_quality" in mod.thresholds
    t = mod.thresholds["booking_quality"]
    assert "min" in t
    assert "max_regression" in t


def test_cost_thresholds_has_cost_per_session():
    """§14.11: cost_thresholds must cover cost_usd_per_session."""
    mod = _load_module()
    assert "cost_usd_per_session" in mod.cost_thresholds


def test_gate_result_dataclass_importable():
    """§14.11: GateResult must be a dataclass with passed and lane_results."""
    mod = _load_module()
    result = mod.GateResult(passed=True, lane_results={})
    assert result.passed is True
    assert result.lane_results == {}


def test_gate_passes_all_lanes():
    """§14.11: gate passes when quality, safety, cost, and policy all pass."""
    mod = _load_module()
    result = mod.run_promotion_gate(
        quality_scores={"booking_quality": 0.90},
        safety_results={"no_prompt_injection": True},
        cost_metrics={"cost_usd_per_session": 0.30},
        policy_checks={"gdpr_compliant": True},
        baseline_scores={"booking_quality": 0.90},
    )
    assert result.passed is True


def test_gate_blocks_quality_below_floor():
    """§14.11: gate blocks when booking_quality is below the 0.87 floor."""
    mod = _load_module()
    result = mod.run_promotion_gate(
        quality_scores={"booking_quality": 0.80},
        safety_results={"no_prompt_injection": True},
        cost_metrics={"cost_usd_per_session": 0.30},
        policy_checks={"gdpr_compliant": True},
        baseline_scores={"booking_quality": 0.80},
    )
    assert result.passed is False
    assert result.lane_results["quality"]["passed"] is False


def test_gate_blocks_regression_exceeds_limit():
    """§14.11: gate blocks when regression exceeds max_regression (0.03)."""
    mod = _load_module()
    result = mod.run_promotion_gate(
        # quality is above floor but regressed 0.05 from baseline
        quality_scores={"booking_quality": 0.88},
        safety_results={"no_prompt_injection": True},
        cost_metrics={"cost_usd_per_session": 0.30},
        policy_checks={"gdpr_compliant": True},
        baseline_scores={"booking_quality": 0.93},
    )
    assert result.passed is False


def test_gate_blocks_safety_failure():
    """§14.11: gate blocks when any safety check fails."""
    mod = _load_module()
    result = mod.run_promotion_gate(
        quality_scores={"booking_quality": 0.90},
        safety_results={"no_prompt_injection": False},
        cost_metrics={"cost_usd_per_session": 0.30},
        policy_checks={"gdpr_compliant": True},
        baseline_scores={"booking_quality": 0.90},
    )
    assert result.passed is False
    assert result.lane_results["safety"]["passed"] is False


def test_gate_blocks_cost_over_ceiling():
    """§14.11: gate blocks when cost_usd_per_session exceeds 0.50."""
    mod = _load_module()
    result = mod.run_promotion_gate(
        quality_scores={"booking_quality": 0.90},
        safety_results={"no_prompt_injection": True},
        cost_metrics={"cost_usd_per_session": 0.75},  # over 0.50 ceiling
        policy_checks={"gdpr_compliant": True},
        baseline_scores={"booking_quality": 0.90},
    )
    assert result.passed is False
    assert result.lane_results["cost"]["passed"] is False
