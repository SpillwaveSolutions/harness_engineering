from __future__ import annotations

import os
import sys
from datetime import date

import anthropic
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from pydantic import BaseModel, Field, field_validator

tracer = trace.get_tracer(__name__)


class SearchFlightsArgs(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    date: date

    @field_validator("date")
    @classmethod
    def must_not_be_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("date must not be in the past")
        return v


class BookFlightArgs(BaseModel):
    flight_id: str = Field(min_length=1)
    passenger_name: str = Field(min_length=1, max_length=100)


ARG_MODELS = {
    "search_flights": SearchFlightsArgs,
    "book_flight": BookFlightArgs,
}

TOOLS = [
    {
        "name": "search_flights",
        "description": "Search flights between two cities for a date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
    {
        "name": "book_flight",
        "description": "Book a specific flight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id": {"type": "string"},
                "passenger_name": {"type": "string"},
            },
            "required": ["flight_id", "passenger_name"],
        },
    },
]


def _live_enabled() -> bool:
    return (
        os.environ.get("HARNESS_LIVE_API") == "1"
        and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )


def validate_plan_step(name: str, args: dict) -> tuple[bool, str]:
    """Return (ok, reason). Reason is empty when ok."""
    model = ARG_MODELS.get(name)
    if model is None:
        return False, f"unknown tool: {name}"
    try:
        model(**args)
    except (TypeError, ValueError) as e:
        return False, str(e)
    return True, ""


MAX_TURNS = 10
MAX_HISTORY_TOKENS = 4000


def count_tokens_approx(messages: list) -> int:
    """Rough token estimate (1 token ~ 4 chars). In production, call
    client.messages.count_tokens() for the exact tokenizer count."""
    return sum(len(str(m.get("content", ""))) for m in messages) // 4


def _has_tool_result(message: dict) -> bool:
    """True if this user message carries a tool_result block. Such a
    block must immediately follow the assistant tool_use that produced
    it, so it can never be stranded at the front of the history."""
    content = message.get("content")
    if not isinstance(content, list):
        return False
    return any(
        isinstance(block, dict) and block.get("type") == "tool_result"
        for block in content
    )


def trim_history(messages: list) -> list:
    """Drop oldest non-system turns until under the token budget.

    Trim in tool-pair-safe units: Anthropic requires a tool_result to
    immediately follow the assistant tool_use that produced it, so
    dropping a lone assistant message would orphan the tool_result
    behind it and make the whole history invalid. After each eviction
    we drop any now-orphaned tool_result too. Harness code has
    contracts of its own; this is one of them.
    """
    if messages and messages[0].get("role") == "system":
        system, convo = messages[:1], messages[1:]
    else:
        system, convo = [], messages[:]
    while (
        count_tokens_approx(system + convo) > MAX_HISTORY_TOKENS
        and len(convo) > 1
    ):
        convo = convo[1:]
        while convo and _has_tool_result(convo[0]):
            convo = convo[1:]
    return system + convo


def dispatch(name: str, args: dict) -> str:
    """Stub implementation. Replace with real API calls in production."""
    if name == "search_flights":
        return '{"flights": [{"id": "AA42", "price": 312}]}'
    if name == "book_flight":
        flight_id = args.get("flight_id", "")
        return f'{{"status": "confirmed", "id": "{flight_id}"}}'
    return '{"error": "unknown tool"}'


def execute_tool_call(
    tool_use_id: str, name: str, args: dict
) -> dict:
    """Dispatch one validated tool call inside its own span.

    Wrap dispatch in try/except so a raising tool still closes its span
    (the `with` block is the finally) and still feeds the failure back
    to the model as a tool_result with is_error=True, the same shape
    the validator uses when it rejects a call. Without this guard an
    exception would skip the span bookkeeping exactly when it matters.
    """
    with tracer.start_as_current_span(f"tool.{name}") as tool_span:
        try:
            content = dispatch(name, args)
            tool_span.set_attribute("tool.success", True)
            is_error = False
        except (TypeError, ValueError, KeyError) as exc:
            tool_span.set_status(Status(StatusCode.ERROR, str(exc)))
            tool_span.set_attribute("tool.success", False)
            tool_span.record_exception(exc)
            content, is_error = f"tool error: {exc}", True
    block = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
    }
    if is_error:
        block["is_error"] = True
    return {"role": "user", "content": [block]}


def run_harnessed(user_msg: str) -> str:
    if not _live_enabled():
        print(
            "offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY "
            "to call the model.",
            file=sys.stderr,
        )
        return f"offline reply: {user_msg}"
    client = anthropic.Anthropic()
    with tracer.start_as_current_span("agent.turn") as turn:
        turn.set_attribute("gen_ai.provider.name", "anthropic")
        turn.set_attribute("gen_ai.request.model", "claude-sonnet-4-6")
        messages = [{"role": "user", "content": user_msg}]
        for _step in range(MAX_TURNS):
            messages = trim_history(messages)
            with tracer.start_as_current_span("model.call"):
                resp = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    tools=TOOLS,
                    messages=messages,
                )
            if resp.stop_reason != "tool_use":
                return resp.content[0].text
            tool_use = next(
                b for b in resp.content if b.type == "tool_use"
            )
            messages.append(
                {"role": "assistant", "content": resp.content}
            )
            ok, reason = validate_plan_step(
                tool_use.name, tool_use.input
            )
            if not ok:
                with tracer.start_as_current_span(
                    f"tool.{tool_use.name}"
                ) as span:
                    span.set_status(Status(StatusCode.ERROR, reason))
                    span.set_attribute("tool.success", False)
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": f"validation error: {reason}",
                        "is_error": True,
                    }],
                })
                continue
            messages.append(
                execute_tool_call(
                    tool_use.id, tool_use.name, tool_use.input
                )
            )
        raise RuntimeError(
            f"agent did not converge in {MAX_TURNS} steps"
        )


def main() -> None:
    ok, reason = validate_plan_step(
        "search_flights",
        {
            "origin": "SFO",
            "destination": "JFK",
            "date": "2099-12-31",
        },
    )
    print(f"valid={ok} reason={reason!r}")
    print(run_harnessed("Book a flight to Lisbon."))


if __name__ == "__main__":
    main()
