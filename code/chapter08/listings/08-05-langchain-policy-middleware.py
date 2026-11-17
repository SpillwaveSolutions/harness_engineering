"""Call budgets enforced by middleware."""

from __future__ import annotations

from deepagents import create_deep_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
)


def search_flights(origin: str, destination: str) -> str:
    """Search flights. Offline result, no network."""
    return f"offline:{origin}:{destination}"


def book_flight(flight_id: str) -> dict:
    """Book a flight. Offline result, no network."""
    return {
        "booking_reference": "OFFLINE-DEMO",
        "flight_id": flight_id,
    }


model_limit = ModelCallLimitMiddleware(run_limit=20)
tool_limit = ToolCallLimitMiddleware(run_limit=50)
agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[search_flights, book_flight],
    system_prompt="Stay inside the call budget.",
    middleware=[model_limit, tool_limit],
)


def main() -> None:
    print(model_limit.run_limit)
    print(tool_limit.run_limit)
    print(book_flight("AA100")["flight_id"])


if __name__ == "__main__":
    main()
