"""Route a query to static hybrid, graph synthesis, or agentic search."""

from __future__ import annotations

import os
import sys
from enum import Enum

import anthropic


class RetrievalRoute(Enum):
    STATIC_HYBRID = "static_hybrid"
    AGENTIC_SEARCH = "agentic_search"
    GRAPH_RAG = "graph_rag"


def classify_query(
    query: str,
    corpus_tag: str,
    has_graph_index: bool = False,
) -> RetrievalRoute:
    """
    Three-tier routing policy for travel_booking_agent retrieval.
    Stable, structured corpora          -> static hybrid.
    Entity-rich corpus-level synthesis  -> GraphRAG when the graph
                                           index is built, else falls
                                           through to agentic search.
    Volatile, exploratory corpora       -> agentic search.
    """
    stable_corpus_tags = {"flight_schedules", "loyalty_program_rules"}
    if corpus_tag in stable_corpus_tags:
        return RetrievalRoute.STATIC_HYBRID
    synthesis_corpus_tags = {"alliance_partner_graph", "fare_rule_graph"}
    if corpus_tag in synthesis_corpus_tags:
        return (
            RetrievalRoute.GRAPH_RAG
            if has_graph_index
            else RetrievalRoute.AGENTIC_SEARCH
        )
    return RetrievalRoute.AGENTIC_SEARCH


def retrieve(
    query: str,
    corpus_tag: str,
    corpus_dir: str,
    hybrid_index,
    graph_index=None,
) -> list[str]:
    route = classify_query(
        query, corpus_tag, has_graph_index=graph_index is not None
    )
    if route == RetrievalRoute.STATIC_HYBRID:
        return hybrid_index.search(query, top_k=20)
    if route == RetrievalRoute.GRAPH_RAG:
        return graph_index.synthesize(query)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline agentic result",
            file=sys.stderr,
        )
        return [query]
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": f"{query}\ncorpus:{corpus_dir}",
            }
        ],
    )
    text = response.content[0].text.strip()
    return [text] if text else [query]


def main() -> None:
    route = classify_query("next flight", "flight_schedules")
    print(route.value)
    found = retrieve(
        "gate change", "airport_operations", "/tmp/corpus", None
    )
    print(found)


if __name__ == "__main__":
    main()
