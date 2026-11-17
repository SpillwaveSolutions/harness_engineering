"""Refund cap, then mask card numbers, with call budgets."""

from __future__ import annotations

import re

from deepagents import create_deep_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    wrap_tool_call,
)

PAN_PATTERN = re.compile(r"\b(\d{6})\d{6,9}(\d{4})\b")
SSN_PATTERN = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")


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
def full_validation_stack(request, handler):
    if request.tool_name == "issue_refund":
        amount = request.tool_input.get("amount", 0)
        if amount > 500:
            return {
                "error": f"Refund ${amount:.2f} exceeds $500 cap",
                "is_error": True,
            }
    result = handler(request)
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        content = PAN_PATTERN.sub(r"\1××××××\2", content)
        content = SSN_PATTERN.sub("[SSN REDACTED]", content)
        result = {**result, "content": content}
    return result


model_limit = ModelCallLimitMiddleware(run_limit=20)
tool_limit = ToolCallLimitMiddleware(run_limit=50)
agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[search_flights, book_flight, issue_refund],
    system_prompt="Validate refunds and redact card numbers.",
    middleware=[model_limit, tool_limit, full_validation_stack],
)


def main() -> None:
    print(book_flight("AA100")["booking_reference"])
    print(model_limit.run_limit)


if __name__ == "__main__":
    main()
