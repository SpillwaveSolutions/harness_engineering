"""Listing 05-07: Boundary-trim hook for verbose tool outputs.

Travel-booking variant. The agent's `search_flights` tool returns a JSON
object with ~40 fields per flight; the booking decision only needs five.
The PostToolUse hook filters at the boundary so the discarded fields
never enter the model's context window.

Mirrors the representative block in book/chapter05.md §5.7.
"""

from __future__ import annotations

from typing import Any

# The allowlist: only these fields from search_flights enter context.
FLIGHT_ALLOWED_FIELDS = {
    "flight_number", "airline", "price_usd",
    "departure_time", "stops",
}


def trim_flight_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    """Strip verbose tool output to the allowlisted fields only."""
    return {
        k: raw_result[k]
        for k in FLIGHT_ALLOWED_FIELDS
        if k in raw_result
    }


def post_tool_use_hook(tool_name: str, tool_result: Any) -> Any:
    """
    PostToolUse hook: intercept raw output, return trimmed payload.
    The model never sees the discarded fields.

    Named tools get their specific reducer; everything else gets a
    character cap so a runaway tool can't blow the context budget.
    """
    if tool_name == "search_flights":
        return trim_flight_result(tool_result)
    if isinstance(tool_result, str) and len(tool_result) > 30_000:
        return tool_result[:30_000] + "\n[output trimmed at boundary]"
    return tool_result


def main() -> None:
    raw = {
        "flight_number": "UA1182",
        "airline": "United",
        "price_usd": 312,
        "departure_time": "2026-05-29T07:15:00-07:00",
        "stops": 0,
        "internal_yield_class": "Q",
    }
    trimmed = post_tool_use_hook("search_flights", raw)
    print(trimmed["flight_number"], trimmed["price_usd"])
    print("internal_yield_class" in trimmed)


if __name__ == "__main__":
    main()
