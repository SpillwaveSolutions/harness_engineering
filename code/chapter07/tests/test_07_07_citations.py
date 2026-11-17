"""Tests for listing 07-07-citations."""

from __future__ import annotations

import os

import pytest


def test_query_with_citations_offline(load_listing, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("07-07-citations")
    result = module.query_with_citations(
        "growth?",
        [{"title": "ACME", "content": "Revenue grew."}],
    )
    assert result == {
        "answer": "growth?",
        "citations": [
            {
                "cited_text": "Revenue grew.",
                "document_title": "ACME",
                "document_index": 0,
            }
        ],
    }


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_query_returns_answer_and_citations_shape(load_listing) -> None:
    module = load_listing("07-07-citations")
    result = module.query_with_citations(
        query="What is the company's Q2 revenue growth?",
        retrieved_chunks=[
            {
                "title": "ACME Q2 2026 Filing",
                "content": "Revenue grew by 3 percent.",
            }
        ],
    )
    assert "answer" in result
    assert isinstance(result["citations"], list)
