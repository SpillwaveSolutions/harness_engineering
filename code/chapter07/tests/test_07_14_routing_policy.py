"""Tests for listing 07-14-routing-policy.

classify_query and RetrievalRoute are pure-logic and require no API key.
The retrieve() function's agentic branch ends in ellipsis (representative-
only); only the static-hybrid branch is exercised here with a stub index.
"""

from __future__ import annotations


def test_module_defines_router(load_listing) -> None:
    """Listing exposes RetrievalRoute, classify_query, and retrieve."""
    module = load_listing("07-14-routing-policy")
    assert hasattr(module, "RetrievalRoute")
    assert callable(module.classify_query)
    assert callable(module.retrieve)


def test_stable_corpus_routes_to_static_hybrid(load_listing) -> None:
    """flight_schedules and loyalty_program_rules are stable → static hybrid."""
    module = load_listing("07-14-routing-policy")
    assert module.classify_query(
        "next flight from LHR to EWR",
        corpus_tag="flight_schedules",
    ) == module.RetrievalRoute.STATIC_HYBRID
    assert module.classify_query(
        "what is the silver-tier upgrade threshold",
        corpus_tag="loyalty_program_rules",
    ) == module.RetrievalRoute.STATIC_HYBRID


def test_volatile_corpus_routes_to_agentic_search(load_listing) -> None:
    """airport_operations and unknown tags are volatile → agentic search."""
    module = load_listing("07-14-routing-policy")
    assert module.classify_query(
        "current NOTAM impact on JFK departures",
        corpus_tag="airport_operations",
    ) == module.RetrievalRoute.AGENTIC_SEARCH
    assert module.classify_query(
        "any-old-query",
        corpus_tag="something_not_in_the_stable_set",
    ) == module.RetrievalRoute.AGENTIC_SEARCH


def test_static_branch_calls_index_search(load_listing) -> None:
    """retrieve() with a stable corpus tag dispatches to hybrid_index.search."""
    module = load_listing("07-14-routing-policy")

    class StubIndex:
        def __init__(self) -> None:
            self.calls: list[tuple[str, int]] = []

        def search(self, query: str, top_k: int = 20) -> list[str]:
            self.calls.append((query, top_k))
            return ["chunk-a", "chunk-b"]

    idx = StubIndex()
    result = module.retrieve(
        query="next flight from LHR to EWR",
        corpus_tag="flight_schedules",
        corpus_dir="/tmp/corpus",
        hybrid_index=idx,
    )
    assert result == ["chunk-a", "chunk-b"]
    assert idx.calls == [("next flight from LHR to EWR", 20)]


def test_synthesis_corpus_routes_to_graph_rag_when_index_present(
    load_listing,
) -> None:
    """Entity-synthesis corpus + graph index built → GraphRAG (tier 3)."""
    module = load_listing("07-14-routing-policy")
    assert module.classify_query(
        "how do alliance partners share fare rules across the network",
        corpus_tag="alliance_partner_graph",
        has_graph_index=True,
    ) == module.RetrievalRoute.GRAPH_RAG


def test_synthesis_corpus_falls_through_without_graph_index(
    load_listing,
) -> None:
    """Entity-synthesis corpus but no graph index → agentic search."""
    module = load_listing("07-14-routing-policy")
    assert module.classify_query(
        "how do alliance partners share fare rules across the network",
        corpus_tag="alliance_partner_graph",
        has_graph_index=False,
    ) == module.RetrievalRoute.AGENTIC_SEARCH


def test_agentic_branch_returns_the_query_offline(
    load_listing, monkeypatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("07-14-routing-policy")
    result = module.retrieve(
        query="current NOTAM",
        corpus_tag="airport_operations",
        corpus_dir="/tmp/corpus",
        hybrid_index=None,
    )
    assert result == ["current NOTAM"]


def test_graph_rag_branch_calls_synthesize(load_listing) -> None:
    """retrieve() with a graph index dispatches to graph_index.synthesize."""
    module = load_listing("07-14-routing-policy")

    class StubGraph:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def synthesize(self, query: str) -> list[str]:
            self.calls.append(query)
            return ["entity-synthesis-result"]

    graph = StubGraph()
    result = module.retrieve(
        query="multi-hop fare-rule reasoning",
        corpus_tag="fare_rule_graph",
        corpus_dir="/tmp/corpus",
        hybrid_index=None,
        graph_index=graph,
    )
    assert result == ["entity-synthesis-result"]
    assert graph.calls == ["multi-hop fare-rule reasoning"]
