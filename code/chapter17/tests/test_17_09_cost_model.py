"""Tests for listing 17-09-cost-model.yaml.

Verifies internal math consistency across the three cost layers:
runtime_cost.monthly_estimate_usd must equal
  monthly_invocations * per_invocation_usd,
operational_cost.monthly_estimate_usd must equal the formula
  (incidents_per_month * hours_per_incident
   + model_swaps_per_year / 12 * hours_per_model_swap
   + regression_review_hours_per_month)
  * engineer_hourly_rate_usd,
and total_monthly_usd must equal the sum of the three layers.
"""

from __future__ import annotations

import math
import pathlib

import pytest
import yaml

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = (
    _CHAPTER_ROOT / "listings" / "17-09-cost-model.yaml"
)

TOLERANCE = 1.0  # USD; rounding allowed within $1


@pytest.fixture(scope="module")
def model() -> dict:
    """Load the YAML cost model once per test session."""
    return yaml.safe_load(_LISTING_PATH.read_text())


def test_listing_file_exists():
    """YAML listing must be present on disk."""
    assert _LISTING_PATH.exists(), f"Missing: {_LISTING_PATH}"


def test_runtime_cost_math(model: dict) -> None:
    """runtime_cost.monthly_estimate_usd must match formula.

    monthly_estimate_usd = monthly_invocations * per_invocation_usd
    """
    rc = model["runtime_cost"]
    expected = rc["monthly_invocations"] * rc["per_invocation_usd"]
    actual = rc["monthly_estimate_usd"]
    assert math.isclose(actual, expected, abs_tol=TOLERANCE), (
        f"runtime_cost math: {rc['monthly_invocations']} x "
        f"{rc['per_invocation_usd']} = {expected:.2f}, "
        f"but monthly_estimate_usd = {actual}"
    )


def test_operational_cost_math(model: dict) -> None:
    """operational_cost.monthly_estimate_usd must match formula.

    = (incidents_per_month * hours_per_incident
       + model_swaps_per_year / 12 * hours_per_model_swap
       + regression_review_hours_per_month)
      * engineer_hourly_rate_usd
    """
    oc = model["operational_cost"]
    monthly_swap_hours = (
        oc["model_swaps_per_year"] / 12 * oc["hours_per_model_swap"]
    )
    total_hours = (
        oc["incidents_per_month"] * oc["hours_per_incident"]
        + monthly_swap_hours
        + oc["regression_review_hours_per_month"]
    )
    expected = total_hours * oc["engineer_hourly_rate_usd"]
    actual = oc["monthly_estimate_usd"]
    assert math.isclose(actual, expected, abs_tol=TOLERANCE), (
        f"operational_cost math: "
        f"({oc['incidents_per_month']}*{oc['hours_per_incident']}"
        f" + {oc['model_swaps_per_year']}/12*{oc['hours_per_model_swap']}"
        f" + {oc['regression_review_hours_per_month']}) "
        f"* {oc['engineer_hourly_rate_usd']} = {expected:.2f}, "
        f"but monthly_estimate_usd = {actual}"
    )


def test_total_monthly_usd_is_sum_of_layers(model: dict) -> None:
    """total_monthly_usd must equal sum of the three layer estimates."""
    expected = (
        model["token_cost"]["monthly_estimate_usd"]
        + model["runtime_cost"]["monthly_estimate_usd"]
        + model["operational_cost"]["monthly_estimate_usd"]
    )
    actual = model["total_monthly_usd"]
    assert math.isclose(actual, expected, abs_tol=TOLERANCE), (
        f"total_monthly_usd: "
        f"{model['token_cost']['monthly_estimate_usd']} + "
        f"{model['runtime_cost']['monthly_estimate_usd']} + "
        f"{model['operational_cost']['monthly_estimate_usd']} "
        f"= {expected:.2f}, but total = {actual}"
    )


def test_required_fields_present(model: dict) -> None:
    """All required top-level and nested fields must be present."""
    assert "token_cost" in model
    assert "runtime_cost" in model
    assert "operational_cost" in model
    assert "total_monthly_usd" in model

    tc = model["token_cost"]
    for field in [
        "model", "price_input_per_mtok", "price_output_per_mtok",
        "daily_conversations", "avg_input_tokens", "avg_output_tokens",
        "monthly_estimate_usd",
    ]:
        assert field in tc, f"token_cost missing field: {field}"

    rc = model["runtime_cost"]
    for field in [
        "per_invocation_usd", "monthly_invocations",
        "monthly_estimate_usd",
    ]:
        assert field in rc, f"runtime_cost missing field: {field}"

    oc = model["operational_cost"]
    for field in [
        "incidents_per_month", "hours_per_incident",
        "model_swaps_per_year", "hours_per_model_swap",
        "regression_review_hours_per_month",
        "engineer_hourly_rate_usd", "monthly_estimate_usd",
    ]:
        assert field in oc, f"operational_cost missing field: {field}"
