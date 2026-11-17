"""The two tool descriptions name themselves and point at each other."""

from __future__ import annotations


def test_descriptions_name_the_tools(load_listing) -> None:
    module = load_listing("09-02-tool-description")
    assert "search_flights" in module.SEARCH_FLIGHTS_DESCRIPTION
    assert "search_loyalty_history" in module.SEARCH_FLIGHTS_DESCRIPTION
    loyalty = module.SEARCH_LOYALTY_DESCRIPTION
    assert "search_loyalty_history" in loyalty
    assert "search_flights" in loyalty
