"""Tests for listing 02-03-failure-catch (§2.3 Failure 3, silent error).

Pins the recorded span shape for a failed ``book_flight`` call. The
load-bearing assertion is the asymmetry: the outer ``agent.turn`` span
closes OK while the inner ``tool.book_flight`` span records ERROR. That
is the difference between a dashboard that says everything is fine and
a dashboard that surfaces the booking failure.
"""

from __future__ import annotations


def test_record_failed_span_marks_inner_tool_span_error(load_listing):
    """§2.3: the inner tool span carries the failure even though the
    outer turn returned cleanly."""
    listing = load_listing("02-03-failure-catch")
    span = listing.record_failed_span()

    assert span["name"] == "agent.turn"
    tool_spans = [
        c for c in span["children"] if c["name"] == "tool.book_flight"
    ]
    assert len(tool_spans) == 1
    tool = tool_spans[0]
    assert tool["status"] == "ERROR"
    assert tool["attributes"]["tool.success"] is False
    assert tool["attributes"]["tool.error"] == (
        "Seat unavailable on flight AA1234"
    )


def test_outer_turn_remains_ok_when_inner_tool_errors(load_listing):
    """§2.3: the whole point — the outer span closes OK; only the
    inner tool span surfaces the failure."""
    listing = load_listing("02-03-failure-catch")
    span = listing.record_failed_span()

    assert span["status"] == "OK"
    inner_statuses = {c["status"] for c in span["children"]}
    assert "ERROR" in inner_statuses
    assert "OK" in inner_statuses


def test_failed_span_carries_exception_payload(load_listing):
    """§2.3: a recorded exception travels alongside the status flag so
    a debugger replaying the trace sees both the structural error
    status and the originating ValueError."""
    listing = load_listing("02-03-failure-catch")
    span = listing.record_failed_span()

    tool = next(
        c for c in span["children"] if c["name"] == "tool.book_flight"
    )
    assert tool["exception"] == (
        "ValueError('Seat unavailable on flight AA1234')"
    )


def test_error_message_override(load_listing):
    """§2.3: callers can drive different failure scenarios — the shape
    of the recorded span is the same; only the payload changes."""
    listing = load_listing("02-03-failure-catch")
    span = listing.record_failed_span(
        flight_id="UA999", error_msg="Card declined"
    )

    tool = next(
        c for c in span["children"] if c["name"] == "tool.book_flight"
    )
    assert tool["attributes"]["tool.error"] == "Card declined"
    assert tool["attributes"]["flight_id"] == "UA999"
