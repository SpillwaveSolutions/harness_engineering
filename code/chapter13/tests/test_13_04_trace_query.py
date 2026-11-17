"""Tests for listing 13-04-trace-query (§13.4).

The listing is SQL (stored as .txt); it cannot be executed by pytest directly.
These tests verify the listing file is present and contains the expected
OTel GenAI attribute references, confirming the query shape matches the
prose claims in §13.4.

Code-test-plan kind: static content validation (custom).
"""

from __future__ import annotations

import pathlib

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"
LISTING_PATH = LISTINGS_DIR / "13-04-trace-query.txt"


@pytest.fixture
def sql_text():
    if not LISTING_PATH.exists():
        pytest.fail(f"SQL listing not found at {LISTING_PATH}")
    return LISTING_PATH.read_text()


def test_listing_exists(sql_text):
    """§13.4: 13-04-trace-query.txt must exist and be non-empty."""
    assert len(sql_text.strip()) > 0


def test_selects_from_spans_table(sql_text):
    """§13.4: query must select FROM spans (the OTel span store table)."""
    assert "FROM spans" in sql_text


def test_filters_on_conversation_id(sql_text):
    """§13.4: query must filter on gen_ai.conversation.id to scope a session."""
    assert "gen_ai.conversation.id" in sql_text


def test_filters_on_execute_tool_span_name(sql_text):
    """§13.4: query must filter on span_name LIKE 'execute_tool%'."""
    assert "execute_tool" in sql_text


def test_returns_error_type_attribute(sql_text):
    """§13.4: query must return error.type to surface the silent_tool_error."""
    assert "error.type" in sql_text


def test_returns_tool_call_result(sql_text):
    """§13.4: query must return gen_ai.tool.call.result to show payload."""
    assert "gen_ai.tool.call.result" in sql_text
