"""Listing 05-07: Search-result cap for the travel-booking agent.

A search that returns more than SEARCH_RESULT_CAP results floods the context
window with low-signal tokens. The cap rejects oversized sets immediately,
swapping a noisy list for a structured 'too_many_results' shape that keeps
context pressure bounded no matter how broad the route.
"""

from typing import Any

SEARCH_RESULT_CAP = 50  # Reject result sets larger than this.


def search_flights(
    origin: str, destination: str, raw_results: list[dict[str, Any]]
) -> dict[str, Any]:
    """Cap flight-search match count before results enter context.

    Returns a structured 'too_many_results' shape when the result set
    exceeds SEARCH_RESULT_CAP, including the count and a suggestion string
    so the model can narrow its next query rather than retrying blindly.
    """
    if len(raw_results) > SEARCH_RESULT_CAP:  # ①
        return {
            "status": "too_many_results",
            "count": len(raw_results),
            "suggestion": (
                f"{len(raw_results)} flights matched {origin}->"
                f"{destination}. Add a time window or fare class."
            ),
        }
    return {"status": "ok", "results": raw_results}  # ②


def main() -> None:
    rows = [{"id": index} for index in range(51)]
    result = search_flights("SFO", "JFK", rows)
    print(result["status"])
    print(result["count"])
    print(result["suggestion"])


if __name__ == "__main__":
    main()
