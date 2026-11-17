"""Listing 2.3 - Failure catch.

Records the inner ``tool.book_flight`` span as ERROR even when the outer
``agent.turn`` closes OK. The point of the listing: the dashboard sees
OK on the turn; per-tool telemetry surfaces the booking failure that
the agent itself summarised as "all set."

Pure Python (no OpenTelemetry SDK dependency at import time) so the test
suite can introspect the recorded span shape directly. The production
runnable form would wire these dataclasses to real ``Status`` /
``StatusCode`` values from ``opentelemetry.trace`` - the shape is the
same; only the host changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ToolSpan:
    name: str
    status: str = "OK"
    attributes: dict[str, Any] = field(default_factory=dict)
    exception: str | None = None


@dataclass
class TurnSpan:
    name: str
    status: str = "OK"
    children: list[Any] = field(default_factory=list)


def record_failed_span(
    flight_id: str = "AA1234",
    error_msg: str = "Seat unavailable on flight AA1234",
) -> dict[str, Any]:
    """Build the agent.turn -> model.call -> tool.book_flight span tree
    for a failed booking. The outer turn closes OK; the inner tool span
    records ERROR so the next debugger sees the failure even when the
    agent's final response did not surface it."""
    turn = TurnSpan(name="agent.turn", status="OK")
    turn.children.append(TurnSpan(name="model.call", status="OK"))

    tool = ToolSpan(name="tool.book_flight", status="ERROR")
    tool.attributes["tool.success"] = False
    tool.attributes["tool.error"] = error_msg
    tool.attributes["flight_id"] = flight_id
    tool.exception = f"ValueError({error_msg!r})"
    turn.children.append(tool)

    turn.children.append(TurnSpan(name="model.call", status="OK"))

    return {
        "name": turn.name,
        "status": turn.status,
        "children": [asdict(child) for child in turn.children],
    }


def main() -> None:
    import json

    print(json.dumps(record_failed_span(), indent=2))


if __name__ == "__main__":
    main()
