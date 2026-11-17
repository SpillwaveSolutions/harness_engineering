"""Keep only book_flight available on the booking step."""

from __future__ import annotations

from deepagents import create_deep_agent
from langchain.agents.middleware import wrap_model_call


def search_flights(origin: str, destination: str) -> str:
    """Search flights. Offline result, no network."""
    return f"offline:{origin}:{destination}"


def book_flight(flight_id: str, passenger_name: str = "Ada") -> dict:
    """Book a flight. Offline result, no network."""
    return {
        "booking_reference": "OFFLINE-DEMO",
        "flight_id": flight_id,
        "passenger_name": passenger_name,
    }


@wrap_model_call
def force_booking_tool(request, handler):
    request.tools = [
        item for item in request.tools if item.name == "book_flight"
    ]
    request.tool_choice = "required"
    return handler(request)


agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[search_flights, book_flight],
    system_prompt="Book the flight the customer confirmed.",
    middleware=[force_booking_tool],
)


def main() -> None:
    print(book_flight("AA100")["booking_reference"])
    print(search_flights("JFK", "LHR"))


if __name__ == "__main__":
    main()
