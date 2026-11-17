"""Tests for listing 07-04-contextual-chunk."""

from __future__ import annotations

import os

import pytest


def test_augment_chunk_offline(load_listing, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("07-04-contextual-chunk")
    raw = "Revenue grew by 3 percent over the previous quarter."
    augmented = module.augment_chunk(raw, "ACME Q2", None)
    assert augmented == f"Context from ACME Q2.\n\n{raw}"


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_augment_chunk_prepends_context(load_listing) -> None:
    import anthropic

    module = load_listing("07-04-contextual-chunk")
    client = anthropic.Anthropic()
    raw = "Revenue grew by 3 percent over the previous quarter."
    augmented = module.augment_chunk(raw, "ACME Corp Q2 2026", client)
    assert raw in augmented
    assert augmented != raw
