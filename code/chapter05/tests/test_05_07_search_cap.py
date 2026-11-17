"""Tests for listing 05-07-search-cap.

Covers the three cases named in the action_item:
  (a) result sets at the cap boundary pass through with status='ok'
  (b) result sets above the cap return status='too_many_results' with a suggestion string
  (c) the suggestion string includes the count and the route (origin->destination)
"""

from __future__ import annotations


def _make_flight(n: int) -> dict:
    """Build a minimal flight dict for testing."""
    return {"flight_id": f"FL{n:04d}", "origin": "SFO", "destination": "JFK"}


def _flights(count: int) -> list[dict]:
    return [_make_flight(i) for i in range(count)]


# ---------------------------------------------------------------------------
# (a) Result sets at the cap boundary pass through with status='ok'
# ---------------------------------------------------------------------------

def test_empty_results_returns_ok(load_listing) -> None:
    """Zero results returns status='ok'."""
    m = load_listing("05-07-search-cap")
    result = m.search_flights("SFO", "JFK", [])
    assert result["status"] == "ok"
    assert result["results"] == []


def test_one_result_returns_ok(load_listing) -> None:
    """A single result returns status='ok'."""
    m = load_listing("05-07-search-cap")
    flights = _flights(1)
    result = m.search_flights("SFO", "JFK", flights)
    assert result["status"] == "ok"
    assert result["results"] == flights


def test_exactly_cap_results_returns_ok(load_listing) -> None:
    """Exactly SEARCH_RESULT_CAP results pass through with status='ok'."""
    m = load_listing("05-07-search-cap")
    cap = m.SEARCH_RESULT_CAP
    flights = _flights(cap)
    result = m.search_flights("SFO", "JFK", flights)
    assert result["status"] == "ok"
    assert len(result["results"]) == cap


def test_one_below_cap_returns_ok(load_listing) -> None:
    """One fewer than the cap also returns status='ok'."""
    m = load_listing("05-07-search-cap")
    cap = m.SEARCH_RESULT_CAP
    flights = _flights(cap - 1)
    result = m.search_flights("SFO", "JFK", flights)
    assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# (b) Result sets above the cap return status='too_many_results' with suggestion
# ---------------------------------------------------------------------------

def test_one_above_cap_returns_too_many_results(load_listing) -> None:
    """One more than the cap returns status='too_many_results'."""
    m = load_listing("05-07-search-cap")
    cap = m.SEARCH_RESULT_CAP
    flights = _flights(cap + 1)
    result = m.search_flights("SFO", "JFK", flights)
    assert result["status"] == "too_many_results"


def test_large_result_set_returns_too_many_results(load_listing) -> None:
    """A large result set (200 flights) returns status='too_many_results'."""
    m = load_listing("05-07-search-cap")
    flights = _flights(200)
    result = m.search_flights("LAX", "ORD", flights)
    assert result["status"] == "too_many_results"


def test_too_many_results_includes_suggestion_string(load_listing) -> None:
    """Status='too_many_results' response includes a non-empty suggestion string."""
    m = load_listing("05-07-search-cap")
    flights = _flights(m.SEARCH_RESULT_CAP + 5)
    result = m.search_flights("SFO", "JFK", flights)
    assert "suggestion" in result
    assert isinstance(result["suggestion"], str)
    assert len(result["suggestion"]) > 0


# ---------------------------------------------------------------------------
# (c) The suggestion string includes the count and the route
# ---------------------------------------------------------------------------

def test_suggestion_includes_count(load_listing) -> None:
    """The suggestion string includes the number of matched flights."""
    m = load_listing("05-07-search-cap")
    count = m.SEARCH_RESULT_CAP + 10
    flights = _flights(count)
    result = m.search_flights("SFO", "JFK", flights)
    assert str(count) in result["suggestion"]


def test_suggestion_includes_origin_and_destination(load_listing) -> None:
    """The suggestion string includes both origin and destination."""
    m = load_listing("05-07-search-cap")
    flights = _flights(m.SEARCH_RESULT_CAP + 1)
    result = m.search_flights("BOS", "LAX", flights)
    assert "BOS" in result["suggestion"]
    assert "LAX" in result["suggestion"]


def test_suggestion_includes_route_arrow(load_listing) -> None:
    """The suggestion string includes 'origin->destination' route notation."""
    m = load_listing("05-07-search-cap")
    flights = _flights(m.SEARCH_RESULT_CAP + 3)
    result = m.search_flights("DEN", "SEA", flights)
    assert "DEN->SEA" in result["suggestion"]


def test_too_many_results_has_count_field(load_listing) -> None:
    """The too_many_results response includes a 'count' field matching len(raw_results)."""
    m = load_listing("05-07-search-cap")
    n = m.SEARCH_RESULT_CAP + 7
    flights = _flights(n)
    result = m.search_flights("SFO", "JFK", flights)
    assert result["count"] == n


def test_ok_result_does_not_contain_suggestion(load_listing) -> None:
    """A within-cap result set does not include a 'suggestion' key."""
    m = load_listing("05-07-search-cap")
    flights = _flights(m.SEARCH_RESULT_CAP)
    result = m.search_flights("SFO", "JFK", flights)
    assert "suggestion" not in result
    assert "count" not in result
