"""Rerank candidate chunks. Without a key, return the input order."""

from __future__ import annotations

import os
import sys

import cohere


def retrieve_and_rerank(
    query: str,
    candidate_chunks: list[str],
    top_n: int = 20,
) -> list[str]:
    """Rerank hybrid search candidates with a cross-encoder."""
    if not os.environ.get("COHERE_API_KEY"):
        print(
            "COHERE_API_KEY unset; returning input chunks unchanged",
            file=sys.stderr,
        )
        return candidate_chunks[:top_n]
    co = cohere.Client()
    rerank_response = co.rerank(
        model="rerank-v4.0-pro",
        query=query,
        documents=candidate_chunks,
        top_n=top_n,
    )
    return [
        candidate_chunks[result.index]
        for result in rerank_response.results
    ]


def main() -> None:
    print(retrieve_and_rerank("schedule", ["a", "b", "c"], top_n=2))


if __name__ == "__main__":
    main()
