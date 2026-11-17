# Before: Deep Agents registers kwargs callables.
# After: the SDK tools take one args dict and return content.

import os
import sys

# === BEFORE (Deep Agents) ===                                        # ①
from deepagents import create_deep_agent

TRAVEL_SYSTEM_PROMPT = "You are a travel-booking assistant."


async def search_flights(
    origin: str, destination: str, date: str
) -> dict:
    """Search flights. Offline reference, no network."""
    return {
        "status": "offline",
        "reference": "OFFLINE-SEARCH",
        "origin": origin,
        "destination": destination,
        "date": date,
    }


async def book_flight(flight_id: str, passenger_name: str) -> dict:
    """Book a flight. Offline reference, no network."""
    return {
        "status": "offline",
        "reference": "OFFLINE-BOOKING",
        "flight_id": flight_id,
        "passenger_name": passenger_name,
    }


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search_flights, book_flight],  # Python callables directly
    system_prompt=TRAVEL_SYSTEM_PROMPT,
)


# === AFTER (agent SDK) ===                                            # ②
from claude_agent_sdk import (
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    query,
    tool,
)


@tool(
    "search_flights",
    "Search flights for a date.",
    {"origin": str, "destination": str, "date": str},
)
async def sdk_search_flights(args: dict) -> dict:
    """SDK tool. One args dict, content-dict result."""
    text = (
        "offline:OFFLINE-SEARCH "
        f"{args['origin']} {args['destination']} {args['date']}"
    )
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "book_flight",
    "Book a flight for a passenger.",
    {"flight_id": str, "passenger_name": str},
)
async def sdk_book_flight(args: dict) -> dict:
    """SDK tool. One args dict, content-dict result."""
    text = (
        "offline:OFFLINE-BOOKING "
        f"{args['flight_id']} {args['passenger_name']}"
    )
    return {"content": [{"type": "text", "text": text}]}


server = create_sdk_mcp_server(
    "travel",
    tools=[sdk_search_flights, sdk_book_flight],
)


async def run_after_migration(user_message: str) -> str:
    """Run the travel-booking agent after SDK migration."""
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
            "mcp__travel__search_flights",
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
