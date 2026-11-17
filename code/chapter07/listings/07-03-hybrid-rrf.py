"""BM25 plus vector search, fused with reciprocal rank fusion.

SentenceTransformer is built inside hybrid_search. If the package is
missing or the model weights cannot be downloaded, the function prints
one stderr line and returns the BM25 ranking.
"""

from __future__ import annotations

import sys

import numpy as np
from rank_bm25 import BM25Okapi


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Merge ranked lists by RRF. No score normalization needed."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def hybrid_search(
    query: str,
    corpus: list[str],
    doc_ids: list[str],
    top_k: int = 20,
) -> list[tuple[str, float]]:
    tokenized = [doc.split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.split())
    order = np.argsort(bm25_scores)[::-1]
    bm25_ranked = [doc_ids[i] for i in order]

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        q_emb = model.encode([query])[0]
        d_embs = model.encode(corpus)
        cosine = d_embs @ q_emb
        vector_ranked = [doc_ids[i] for i in np.argsort(cosine)[::-1]]
    except (ImportError, OSError, RuntimeError, ValueError, AttributeError):
        # Missing package or a weight download. BM25 order is deterministic.
        print(
            "sentence-transformers model unavailable; returning BM25 order",
            file=sys.stderr,
        )
        ranked = [
            (doc_ids[int(i)], float(bm25_scores[int(i)])) for i in order
        ]
        return ranked[:top_k]

    fused = reciprocal_rank_fusion([bm25_ranked, vector_ranked])
    return fused[:top_k]


def main() -> None:
    corpus = ["window seat policy", "aisle seat preference"]
    doc_ids = ["doc-window", "doc-aisle"]
    ranked = hybrid_search("aisle seat", corpus, doc_ids, top_k=2)
    print([doc_id for doc_id, _score in ranked])


if __name__ == "__main__":
    main()
