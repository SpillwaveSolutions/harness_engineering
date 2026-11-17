# Travel-booking tools registered as an in-process MCP server
# Capability registry permission scoping maps onto SDK permission layers

import os
import sys

from claude_agent_sdk import (
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)

_SEARCH = (
    "Search available flights between two airports for a given date. "
    "Returns a list of FlightOption objects sorted by price. "
    "Use this before book_flight; do NOT use book_flight without "
    "calling this first to confirm availability."
)
_BOOK = (
    "Book a specific flight for a passenger. Requires a flight_id "
    "returned by search_flights. Irreversible: confirm with the user "
    "before calling."
)


@tool(
    "search_flights",
    _SEARCH,
    {"origin": str, "destination": str, "date": str},
)
async def search_flights(args: dict) -> dict:
    """Search flights. Offline reference, no network."""
    text = (
        "offline:OFFLINE-SEARCH "
        f"{args['origin']} {args['destination']} {args['date']}"
    )
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "book_flight",
    _BOOK,
    {"flight_id": str, "passenger_name": str},
)
async def book_flight(args: dict) -> dict:
    """Book a flight. Offline reference, no network."""
    text = (
        "offline:OFFLINE-BOOKING "
        f"{args['flight_id']} {args['passenger_name']}"
    )
    return {"content": [{"type": "text", "text": text}]}


server = create_sdk_mcp_server(
    "travel",
    tools=[search_flights, book_flight],
)


async def run_agent(user_message: str) -> str:
    """Run the agent. Offline unless HARNESS_LIVE_API=1."""
    if os.environ.get("HARNESS_LIVE_API") != "1":
        print(
            "offline: HARNESS_LIVE_API is not 1",
            file=sys.stderr,
            flush=True,
        )
        return "offline:OFFLINE-BOOKING"
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        allowed_tools=[
            "mcp__travel__search_flights",  # ①
            "mcp__travel__book_flight",
        ],
        mcp_servers={"travel": server},
    )
    text = ""
    async for message in query(
        prompt=user_message, options=options
    ):
        result = getattr(message, "result", None)
        if isinstance(result, str):
            text = result
    return text
