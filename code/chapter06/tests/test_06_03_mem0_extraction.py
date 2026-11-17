"""Tests for listing 06-03-mem0-extraction.

Offline path uses the in-memory fake. Live Mem0 runs only when
HARNESS_LIVE_API=1.
"""

from __future__ import annotations

import os

import pytest


def test_offline_extract_and_retrieve_return_lists(
    load_listing, monkeypatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("06-03-mem0-extraction")
    user_id = "offline-alice"
    stored = module.process_turn_and_extract(
        user_id,
        [{"role": "user", "content": "My favorite color is blue."}],
    )
    assert stored == [
        {"memory": "My favorite color is blue."},
        {"memory": "offline: noted the user turn"},
    ]
    facts = module.retrieve_facts_for_session(
        user_id, "color", top_k=5
    )
    assert facts == ["My favorite color is blue."]


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_live_extract_returns_memory_dicts(load_listing) -> None:
    module = load_listing("06-03-mem0-extraction")
    user_id = "live-alice"
    stored = module.process_turn_and_extract(
        user_id,
        [{"role": "user", "content": "My favorite color is blue."}],
    )
    assert isinstance(stored, list)
    for item in stored:
        assert isinstance(item, dict)
        assert "memory" in item
