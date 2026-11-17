"""Tests for listing 13-06b-cost-promql (§13.6).

The listing is PromQL (stored as .promql); it cannot be executed by pytest
directly. These tests verify the listing file is present and contains the
expected OTel metric and label references described in §13.6.

Code-test-plan kind: static content validation (custom).
"""

from __future__ import annotations

import pathlib

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"
LISTING_PATH = LISTINGS_DIR / "13-06b-cost-promql.promql"


@pytest.fixture
def promql_text():
    if not LISTING_PATH.exists():
        pytest.fail(f"PromQL listing not found at {LISTING_PATH}")
    return LISTING_PATH.read_text()


def test_listing_exists(promql_text):
    """§13.6: 13-06b-cost-promql.promql must exist and be non-empty."""
    assert len(promql_text.strip()) > 0


def test_uses_gen_ai_client_token_usage_metric(promql_text):
    """§13.6: PromQL must reference gen_ai_client_token_usage_count metric."""
    assert "gen_ai_client_token_usage_count" in promql_text


def test_filters_on_input_token_type(promql_text):
    """§13.6: PromQL must filter token_type='input' to compute input-token rate."""
    assert 'token_type="input"' in promql_text


def test_groups_by_model_label(promql_text):
    """§13.6: PromQL must sum by gen_ai_request_model to break down by model."""
    assert "gen_ai_request_model" in promql_text


def test_uses_rate_function(promql_text):
    """§13.6: PromQL must use rate() for a per-second token metric."""
    assert "rate(" in promql_text
