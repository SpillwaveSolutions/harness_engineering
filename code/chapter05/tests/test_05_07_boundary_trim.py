"""Tests for listing 05-07-boundary-trim.

Verifies the boundary-trim hook: FLIGHT_ALLOWED_FIELDS allowlist filtering,
graceful handling of missing keys, dispatch routing for search_flights,
character cap with trim marker, and passthrough of short/non-string
results. Travel-booking domain, matching the chapter's running example.
"""

from __future__ import annotations


def test_trim_flight_result_retains_only_allowed_fields(load_listing) -> None:
    """trim_flight_result keeps only keys present in FLIGHT_ALLOWED_FIELDS."""
    m = load_listing("05-07-boundary-trim")
    raw = {
        "flight_number": "UA1182",
        "airline": "United",
        "price_usd": 312,
        "departure_time": "2026-05-29T07:15:00-07:00",
        "stops": 0,
        "internal_yield_class": "Q",   # not in allowlist
        "fare_basis": "QAA7BNN",       # not in allowlist
    }
    result = m.trim_flight_result(raw)
    assert set(result.keys()) == m.FLIGHT_ALLOWED_FIELDS & set(raw.keys())
    assert "internal_yield_class" not in result
    assert "fare_basis" not in result


def test_trim_flight_result_handles_missing_keys_without_error(load_listing) -> None:
    """trim_flight_result does not raise when allowed keys are absent from input."""
    m = load_listing("05-07-boundary-trim")
    raw = {"flight_number": "UA1182"}  # only one of the five allowed fields
    result = m.trim_flight_result(raw)
    assert result == {"flight_number": "UA1182"}


def test_trim_flight_result_empty_dict(load_listing) -> None:
    """trim_flight_result returns an empty dict when input has no allowed keys."""
    m = load_listing("05-07-boundary-trim")
    result = m.trim_flight_result({})
    assert result == {}


def test_post_tool_use_hook_routes_search_flights(load_listing) -> None:
    """post_tool_use_hook routes 'search_flights' through trim_flight_result."""
    m = load_listing("05-07-boundary-trim")
    raw = {
        "flight_number": "UA1182",
        "airline": "United",
        "internal_yield_class": "Q",
    }
    result = m.post_tool_use_hook("search_flights", raw)
    assert "internal_yield_class" not in result
    assert result.get("flight_number") == "UA1182"


def test_post_tool_use_hook_caps_long_string_for_unknown_tool(load_listing) -> None:
    """post_tool_use_hook applies 30,000-char cap with trim marker for unrecognised tools."""
    m = load_listing("05-07-boundary-trim")
    long_output = "x" * 35_000
    result = m.post_tool_use_hook("some_other_tool", long_output)
    assert len(result) <= 30_000 + len("\n[output trimmed at boundary]")
    assert result.endswith("\n[output trimmed at boundary]")
    assert result.startswith("x" * 100)


def test_post_tool_use_hook_returns_short_string_unchanged(load_listing) -> None:
    """post_tool_use_hook returns strings under 30,000 chars without modification."""
    m = load_listing("05-07-boundary-trim")
    short = "hello world"
    result = m.post_tool_use_hook("any_tool", short)
    assert result == short


def test_post_tool_use_hook_returns_non_string_unchanged(load_listing) -> None:
    """post_tool_use_hook returns non-string results (dict, int, list) unchanged."""
    m = load_listing("05-07-boundary-trim")
    for value in [{"key": "val"}, 42, [1, 2, 3], None]:
        assert m.post_tool_use_hook("any_tool", value) == value
