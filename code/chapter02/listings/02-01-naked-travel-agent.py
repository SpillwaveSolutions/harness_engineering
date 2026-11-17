"""Naked travel-booking loop.

The model client is built only when a live call is actually made.
Importing this file does not read an API key and does not open a
network connection.
"""

from __future__ import annotations

import os
import sys

import anthropic
from anthropic.types import ToolParam

# Typed as list[ToolParam] so `tools=TOOLS` is clean under a static
# type checker: list[dict] is not assignable to Iterable[ToolUnionParam].
TOOLS: list[ToolParam] = [
    {
        "name": "search_flights",
        "description": "Search flights between two cities for a date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
    {
        "name": "book_flight",
        "description": "Book a specific flight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id": {"type": "string"},
                "passenger_name": {"type": "string"},
            },
            "required": ["flight_id", "passenger_name"],
        },
    },
]


def dispatch(name: str, args: dict) -> str:
    """Return a short offline result for one tool call."""
    if name == "search_flights":
        origin = args.get("origin", "")
        destination = args.get("destination", "")
        return f"search_flights: {origin}->{destination}"
    if name == "book_flight":
        return f"book_flight: {args.get('flight_id', '')}"
    return "unknown tool"


def _live_enabled() -> bool:
    return (
        os.environ.get("HARNESS_LIVE_API") == "1"
        and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )


def run_naked(user_msg: str) -> str:
    if not _live_enabled():
        print(
            "offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY "
            "to call the model.",
            file=sys.stderr,
        )
        return f"offline reply: {user_msg}"
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": user_msg}]
    while True:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        if resp.stop_reason != "tool_use":
            return resp.content[0].text
        tool_use = next(b for b in resp.content if b.type == "tool_use")
        result = dispatch(tool_use.name, tool_use.input)
        messages.extend([
            {"role": "assistant", "content": resp.content},
            {"role": "user", "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            }]},
        ])


def main() -> None:
    print(run_naked("Book a flight from SFO to JFK."))


if __name__ == "__main__":
    main()
