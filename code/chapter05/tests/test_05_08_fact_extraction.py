"""Tests for listing 05-08-fact-extraction.

Verifies PersistentFactBlock CRUD, to_context_segment rendering, key
overwrite behaviour, offline fact extraction, and the live
extract_facts_from_turn API call when HARNESS_LIVE_API=1.
"""

from __future__ import annotations

import os

import pytest


def test_update_stores_key_value_pair(load_listing) -> None:
    """PersistentFactBlock.update stores a key-value pair."""
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    fb.update("delivery_date", "2026-06-01")
    assert fb._facts["delivery_date"] == "2026-06-01"


def test_to_context_segment_empty_when_no_facts(load_listing) -> None:
    """to_context_segment returns empty string when no facts have been stored."""
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    assert fb.to_context_segment() == ""


def test_to_context_segment_renders_header_and_facts(load_listing) -> None:
    """to_context_segment renders the PERSISTENT FACTS header and indented key: value lines."""
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    fb.update("refund_deadline", "2026-06-15")
    fb.update("order_total", "$127.50")
    segment = fb.to_context_segment()
    assert "PERSISTENT FACTS" in segment
    assert "  refund_deadline: 2026-06-15" in segment
    assert "  order_total: $127.50" in segment


def test_update_overwrites_existing_key(load_listing) -> None:
    """update replaces the value when the same key is written twice."""
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    fb.update("status", "pending")
    fb.update("status", "shipped")
    assert fb._facts["status"] == "shipped"
    assert list(fb._facts.keys()).count("status") == 1


def test_to_context_segment_multiple_facts_all_present(load_listing) -> None:
    """to_context_segment includes all stored facts when multiple are present."""
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    pairs = {"date": "2026-05-22", "amount": "$500", "name": "Marcus Chen"}
    for k, v in pairs.items():
        fb.update(k, v)
    segment = fb.to_context_segment()
    for k, v in pairs.items():
        assert k in segment
        assert v in segment


def test_extract_facts_offline_returns_dates_and_amount(
    load_listing, monkeypatch, capsys
) -> None:
    """Offline extraction returns fact dicts taken from the message."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = load_listing("05-08-fact-extraction")
    fb = m.PersistentFactBlock()
    turn_text = (
        "I need to return my order by June 15, 2026. "
        "The total was $127.50 and I was charged on May 1, 2026."
    )
    facts = m.extract_facts_from_turn(None, turn_text, fb)
    assert facts == [
        {"date": "June 15, 2026"},
        {"amount": "$127.50"},
        {"date_2": "May 1, 2026"},
    ]
    segment = fb.to_context_segment()
    assert "June 15, 2026" in segment
    assert "$127.50" in segment
    assert "May 1, 2026" in segment
    err = capsys.readouterr().err
    assert "HARNESS_LIVE_API=1" in err
    assert "ANTHROPIC_API_KEY" in err


def test_extract_facts_offline_does_not_call_the_client(
    load_listing, monkeypatch
) -> None:
    """A client object is ignored unless the live flag and key are set."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    m = load_listing("05-08-fact-extraction")

    class _Client:
        def __init__(self) -> None:
            self.calls = 0

        @property
        def messages(self):
            raise AssertionError("messages was touched")

    fb = m.PersistentFactBlock()
    facts = m.extract_facts_from_turn(_Client(), "hello there", fb)
    assert facts == []
    assert fb.to_context_segment() == ""


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="live API test; set HARNESS_LIVE_API=1 to run",
)
def test_extract_facts_from_turn_populates_fact_block(load_listing) -> None:
    """extract_facts_from_turn calls the Anthropic API and stores a date and amount."""
    import anthropic

    m = load_listing("05-08-fact-extraction")
    client = anthropic.Anthropic()
    fb = m.PersistentFactBlock()
    turn_text = (
        "I need to return my order by June 15, 2026. "
        "The total was $127.50 and I was charged on May 1, 2026."
    )
    m.extract_facts_from_turn(client, turn_text, fb)
    segment = fb.to_context_segment()
    # At least one date or dollar value should be captured.
    assert segment != "", "Expected at least one fact to be extracted from the turn."
