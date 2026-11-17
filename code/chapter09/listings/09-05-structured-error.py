from typing import Literal

from pydantic import BaseModel

ErrorCategory = Literal[
    "transient",     # rate limit, timeout — retry with backoff
    "validation",    # malformed input — fix the input
    "permission",    # auth failure — escalate, don't retry
    "business",      # valid request, violates domain rules — escalate
]

class ToolError(BaseModel):
    error_category: ErrorCategory
    is_retryable: bool
    message: str           # agent-facing, structured explanation
    user_message: str      # human-friendly if surfaced to customer

def make_tool_error(
    category: ErrorCategory,
    message: str,
    user_message: str,
) -> dict:
    is_retryable = category == "transient"
    return ToolError(
        error_category=category,
        is_retryable=is_retryable,
        message=message,
        user_message=user_message,
    ).model_dump()

class _Booking:
    def __init__(self, booking_id: str) -> None:
        self.booking_id = booking_id
        self.is_non_refundable = booking_id.startswith("NR-")


def get_booking(booking_id: str) -> _Booking:
    """Local booking lookup. Ids that start with NR- cannot be cancelled."""
    return _Booking(booking_id)


# Example: cancel_booking tool error for a business-rule violation
def cancel_booking(booking_id: str) -> dict:
    booking = get_booking(booking_id)
    if booking.is_non_refundable:
        return make_tool_error(
            category="business",
            message=(
                f"Booking {booking_id} is non-refundable. "
                "The fare class does not permit cancellation. "
                "Offer the customer a date-change instead."
            ),
            user_message=(
                "This booking cannot be cancelled. "
                "Your fare is non-refundable. "
                "We can help you change the date instead."
            ),
        )
    return {"booking_id": booking_id, "status": "cancelled"}


def main() -> None:
    print(cancel_booking("NR-100")["error_category"])
    print(cancel_booking("BK-100")["status"])


if __name__ == "__main__":
    main()
