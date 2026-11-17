"""Deny a refund that exceeds the cap before the tool runs."""

from __future__ import annotations

from deepagents import create_deep_agent
from langchain.agents.middleware import wrap_tool_call

REFUND_CAP_USD = 500.0


def search_flights(origin: str, destination: str) -> str:
    """Search flights. Offline result, no network."""
    return f"offline:{origin}:{destination}"


def book_flight(flight_id: str) -> dict:
    """Book a flight. Offline result, no network."""
    return {
        "booking_reference": "OFFLINE-DEMO",
        "flight_id": flight_id,
    }


def issue_refund(booking_id: str, amount: float) -> str:
    """Issue a refund. Offline result, no network."""
    return f"offline-refund:{booking_id}:{amount:.2f}"


@wrap_tool_call
def enforce_refund_cap(request, handler):
    if request.tool_name == "issue_refund":
        amount = request.tool_input.get("amount", 0)
        if amount > REFUND_CAP_USD:
            return {
                "error": (
                    f"Refund of ${amount:.2f} exceeds the "
                    f"${REFUND_CAP_USD:.2f} cap."
                ),
                "is_error": True,
            }
    return handler(request)


agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[search_flights, book_flight, issue_refund],
    system_prompt="Cap refunds at 500 dollars.",
    middleware=[enforce_refund_cap],
)


def main() -> None:
    print(issue_refund("BK1", 40.0))


if __name__ == "__main__":
    main()
