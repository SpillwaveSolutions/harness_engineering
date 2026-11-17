import json
import os
import sys
import time
import uuid
from typing import Literal

from anthropic import Anthropic
from pydantic import BaseModel, Field

_AUDIT_LOG: list[dict] = []


def append_to_audit_log(entry: dict) -> None:
    """Append one audit record. Local list; no network."""
    _AUDIT_LOG.append(entry)


def get_client() -> Anthropic | None:
    """Build a client only when ANTHROPIC_API_KEY is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; audit log stays local",
            file=sys.stderr,
        )
        return None
    return Anthropic()

# Pydantic model for input validation
class BookFlightInput(BaseModel):
    origin: str = Field(
        ...,
        description="IATA airport code for origin (e.g., 'JFK')",
        pattern=r"^[A-Z]{3}$",
    )
    destination: str = Field(
        ...,
        description="IATA airport code for destination (e.g., 'LHR')",
        pattern=r"^[A-Z]{3}$",
    )
    date: str = Field(
        ...,
        description="Departure date in ISO-8601 format (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    cabin_class: Literal["economy", "premium_economy", "business", "first"] = (
        "economy"
    )

# Schema-driven tool definition (three required fields per MCP spec)
BOOK_FLIGHT_TOOL = {
    "name": "book_flight",
    "description": (
        "Book a flight for the customer. Use this tool only after the "
        "customer has confirmed the flight selection from search_flights. "
        "Requires IATA codes and ISO-8601 date. Returns a booking reference "
        "on success. Do not call without explicit customer confirmation."
    ),
    "input_schema": BookFlightInput.model_json_schema(),
}

# Audit log entry
def write_audit_entry(
    session_id: str,
    tool_name: str,
    caller_identity: str,
    input_validated: dict,
    result_type: str,
    latency_ms: float,
) -> None:
    entry = {
        "audit_id": str(uuid.uuid4()),
        "session_id": session_id,          # CLAUDE_SESSION_ID
        "tool_name": tool_name,
        "caller_identity": caller_identity,
        "input_hash": hash(json.dumps(input_validated, sort_keys=True)),
        "result_type": result_type,         # "success" | "tool_error" | "denied"
        "latency_ms": latency_ms,
        "timestamp": time.time(),
    }
    append_to_audit_log(entry)


def main() -> None:
    get_client()
    write_audit_entry(
        session_id="demo",
        tool_name="book_flight",
        caller_identity="agent",
        input_validated={"origin": "JFK"},
        result_type="success",
        latency_ms=1.0,
    )
    print(_AUDIT_LOG[-1]["tool_name"])
    print(_AUDIT_LOG[-1]["result_type"])


if __name__ == "__main__":
    main()
