"""Force a booking tool through the agent SDK options object."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, tool


@tool(
    "book_flight",
    "Book a confirmed flight for the passenger",
    {
        "flight_id": str,
        "passenger_name": str,
        "cabin_class": {
            "type": "string",
            "enum": [
                "economy",
                "premium_economy",
                "business",
                "first",
            ],
        },
        "price_usd": {
            "type": "number",
            "minimum": 0,
            "maximum": 50000,
        },
    },
)
async def book_flight(args: dict) -> dict:
    flight_id = args.get("flight_id")
    if not flight_id:
        nested = args.get("args")
        if isinstance(nested, dict):
            flight_id = nested.get("flight_id")
        else:
            flight_id = nested
    return {
        "booking_reference": "OFFLINE-DEMO",
        "flight_id": flight_id,
    }


# allowed_tools is the SDK field that names book_flight.
# The options object rejects tool_choice and strict.
options = ClaudeAgentOptions(
    allowed_tools=["book_flight"],
    model="claude-sonnet-4-6",
)


def main() -> None:
    result = asyncio.run(book_flight.handler({"flight_id": "AA100"}))
    print(result["booking_reference"])
    print(result["flight_id"])
    print(options.allowed_tools[0])
    _client_type = ClaudeSDKClient
    print(_client_type.__name__)


if __name__ == "__main__":
    main()
