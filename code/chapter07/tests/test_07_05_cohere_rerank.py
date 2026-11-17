"""Tests for listing 07-05-cohere-rerank."""

from __future__ import annotations

import os

import pytest


def test_rerank_offline_returns_input_prefix(
    load_listing, monkeypatch
) -> None:
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    module = load_listing("07-05-cohere-rerank")
    chunks = [
        "Flights from LHR to EWR depart twice daily.",
        "The Boeing 777 carries up to 396 passengers.",
        "Visa requirements vary by passport country.",
    ]
    assert module.retrieve_and_rerank("LHR", chunks, top_n=2) == chunks[:2]


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_rerank_returns_subset_of_candidates(load_listing) -> None:
    module = load_listing("07-05-cohere-rerank")
    candidates = [
        "Flights from LHR to EWR depart twice daily.",
        "The Boeing 777 carries up to 396 passengers.",
        "Visa requirements for US entry vary by passport country.",
    ]
    top = module.retrieve_and_rerank(
        query="LHR to EWR flight schedule",
        candidate_chunks=candidates,
        top_n=2,
    )
    assert len(top) == 2
    for chunk in top:
        assert chunk in candidates
