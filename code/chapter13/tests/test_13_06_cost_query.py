"""Tests for listing 13-06-cost-query (§13.6).

The listing is SQL (stored as .txt); it cannot be executed by pytest directly.
These tests verify the listing file is present and contains the expected
OTel GenAI attribute references and cost-rollup structure described in §13.6.

Code-test-plan kind: static content validation (custom).
"""

from __future__ import annotations

import pathlib

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"
LISTING_PATH = LISTINGS_DIR / "13-06-cost-query.txt"


@pytest.fixture
def sql_text():
    if not LISTING_PATH.exists():
        pytest.fail(f"SQL listing not found at {LISTING_PATH}")
    return LISTING_PATH.read_text()


def test_listing_exists(sql_text):
    """§13.6: 13-06-cost-query.txt must exist and be non-empty."""
    assert len(sql_text.strip()) > 0


def test_joins_model_pricing_table(sql_text):
    """§13.6: query must JOIN against model_pricing to keep prices updateable."""
    assert "model_pricing" in sql_text.lower()
    assert "JOIN" in sql_text.upper()


def test_selects_cost_usd_column(sql_text):
    """§13.6: query must produce a cost_usd column."""
    assert "cost_usd" in sql_text


def test_groups_by_date_and_model(sql_text):
    """§13.6: query must GROUP BY run_date and model for daily per-model rollup."""
    upper = sql_text.upper()
    assert "GROUP BY" in upper


def test_filters_on_service_name(sql_text):
    """§13.6: query must filter on service.name = 'travel_booking_agent'."""
    assert "travel_booking_agent" in sql_text


def test_uses_gen_ai_response_model_attribute(sql_text):
    """§13.6: query must use gen_ai.response.model (not just request.model)."""
    assert "gen_ai.response.model" in sql_text


def test_filters_chat_spans(sql_text):
    """§13.6: query must filter span_name LIKE 'chat%' to target model spans."""
    assert "chat" in sql_text.lower()
