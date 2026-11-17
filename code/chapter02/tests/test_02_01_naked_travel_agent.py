"""Tests for listing 02-01-naked-travel-agent.

Offline dispatch returns a short string. run_naked echoes the user
text and does not construct a client unless a live call is enabled.
"""

from __future__ import annotations


def test_dispatch_search_and_book(load_listing):
    listing = load_listing("02-01-naked-travel-agent")
    search = listing.dispatch(
        "search_flights",
        {"origin": "SFO", "destination": "JFK"},
    )
    booked = listing.dispatch("book_flight", {"flight_id": "AA42"})
    assert search == "search_flights: SFO->JFK"
    assert booked == "book_flight: AA42"
    assert listing.dispatch("teleport", {}) == "unknown tool"


def test_run_naked_offline_includes_user_text(
    load_listing, monkeypatch, capsys
):
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    listing = load_listing("02-01-naked-travel-agent")

    class Boom:
        def __init__(self, *args, **kwargs):
            raise AssertionError("client constructed")

    monkeypatch.setattr(listing.anthropic, "Anthropic", Boom)
    reply = listing.run_naked("Book a flight to Lisbon")
    assert reply == "offline reply: Book a flight to Lisbon"
    err = capsys.readouterr().err
    assert "HARNESS_LIVE_API=1" in err
    assert "ANTHROPIC_API_KEY" in err
