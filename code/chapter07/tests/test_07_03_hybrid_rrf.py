"""Tests for listing 07-03-hybrid-rrf."""

from __future__ import annotations

import builtins

import numpy as np
import pytest
from rank_bm25 import BM25Okapi


def test_reciprocal_rank_fusion_scores() -> None:
    ranked_lists = [["A", "B", "X"], ["A", "Y", "B", "C"]]
    k = 60
    expected: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            expected[doc_id] = expected.get(doc_id, 0.0) + 1.0 / (k + rank)
    assert max(expected, key=expected.get) == "A"


def test_listing_rrf_matches_formula(load_listing) -> None:
    module = load_listing("07-03-hybrid-rrf")
    fused = module.reciprocal_rank_fusion(
        [["A", "B"], ["A"]], k=60
    )
    assert fused[0] == ("A", pytest.approx(1 / 61 + 1 / 61))
    assert fused[1] == ("B", pytest.approx(1 / 62))


def test_hybrid_search_bm25_fallback(load_listing, monkeypatch) -> None:
    """Weights may be absent. Force the import failure and assert BM25."""
    real_import = builtins.__import__

    def _block(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "sentence_transformers" or name.startswith(
            "sentence_transformers."
        ):
            raise ImportError("model stack unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _block)
    module = load_listing("07-03-hybrid-rrf")
    corpus = ["window seat policy", "aisle seat preference"]
    doc_ids = ["doc-window", "doc-aisle"]
    query = "aisle seat"
    scores = BM25Okapi([doc.split() for doc in corpus]).get_scores(
        query.split()
    )
    order = [int(i) for i in np.argsort(scores)[::-1]]
    ranked = module.hybrid_search(query, corpus, doc_ids, top_k=2)
    assert [doc_id for doc_id, _score in ranked] == [
        doc_ids[i] for i in order
    ]
    assert ranked[0][0] == "doc-aisle"
    assert ranked[0][1] == pytest.approx(float(scores[order[0]]))
