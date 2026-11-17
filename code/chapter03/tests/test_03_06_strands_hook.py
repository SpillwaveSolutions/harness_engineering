"""Tests for listing 03-06-strands-hook.

BookingRulesHook blocks book_flight when passenger_count is above 10
and leaves every other call alone. The event is a simple namespace:
BeforeToolCallEvent also needs an agent instance.
"""

from __future__ import annotations

from types import SimpleNamespace


def _event(name: str, passenger_count: int) -> SimpleNamespace:
    return SimpleNamespace(
        tool_use={
            "name": name,
            "input": {"passenger_count": passenger_count},
        },
        cancel_tool=False,
    )


def test_booking_blocked_when_passenger_count_exceeds_limit(load_listing):
    """passenger_count=11 sets cancel_tool."""
    listing = load_listing("03-06-strands-hook")
    hook = listing.BookingRulesHook()
    event = _event("book_flight", 11)
    hook.validate_booking(event)
    assert event.cancel_tool
    assert "BLOCKED" in event.cancel_tool


def test_booking_blocked_when_passenger_count_well_above_limit(load_listing):
    """passenger_count=15 is blocked and the count is in the message."""
    listing = load_listing("03-06-strands-hook")
    hook = listing.BookingRulesHook()
    event = _event("book_flight", 15)
    hook.validate_booking(event)
    assert event.cancel_tool
    assert "15" in event.cancel_tool
    assert "BLOCKED" in event.cancel_tool


def test_booking_allowed_when_passenger_count_at_limit(load_listing):
    """passenger_count=10 leaves cancel_tool falsy."""
    listing = load_listing("03-06-strands-hook")
    hook = listing.BookingRulesHook()
    event = _event("book_flight", 10)
    hook.validate_booking(event)
    assert not event.cancel_tool


def test_non_flight_tool_is_not_blocked(load_listing):
    """Calls other than book_flight are ignored."""
    listing = load_listing("03-06-strands-hook")
    hook = listing.BookingRulesHook()
    event = _event("search_flights", 99)
    hook.validate_booking(event)
    assert not event.cancel_tool


def test_register_hooks_subscribes_validate_booking(load_listing):
    """register_hooks subscribes validate_booking to BeforeToolCallEvent."""
    listing = load_listing("03-06-strands-hook")

    class _Registry:
        def __init__(self) -> None:
            self.calls: list[tuple] = []

        def add_callback(self, event_type, callback) -> None:
            self.calls.append((event_type, callback))

    hook = listing.BookingRulesHook()
    registry = _Registry()
    hook.register_hooks(registry)
    assert registry.calls == [
        (listing.BeforeToolCallEvent, hook.validate_booking)
    ]
