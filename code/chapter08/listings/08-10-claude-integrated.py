"""Booking step: refund cap, output redaction, then schema check."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    PostToolUseHookInput,
    PreToolUseHookInput,
)
from pydantic import BaseModel, field_validator

REFUND_CAP_USD = 500.0
MAX_RETRIES = 3
PRIMARY_MODEL = "claude-sonnet-4-6"
FALLBACK_MODEL = "claude-haiku-4-5"
PAN_PATTERN = re.compile(r"\b(\d{6})\d{6,9}(\d{4})\b")
SSN_PATTERN = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")


async def enforce_refund_cap(
    input_data: PreToolUseHookInput,
    tool_use_id: str,
    context,
) -> dict:
    if input_data.tool_name != "issue_refund":
        return {}
    amount = input_data.tool_input.get("amount", 0)
    if amount > REFUND_CAP_USD:
        return {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Refund of ${amount:.2f} exceeds the "
                    f"${REFUND_CAP_USD:.2f} cap."
                ),
            }
        }
    return {}


async def sanitize_tool_output(
    input_data: PostToolUseHookInput,
    tool_use_id: str,
    context,
) -> dict:
    if not isinstance(input_data.tool_response, str):
        return {}
    sanitized = PAN_PATTERN.sub(r"\1××××××\2", input_data.tool_response)
    sanitized = SSN_PATTERN.sub("[SSN REDACTED]", sanitized)
    if sanitized == input_data.tool_response:
        return {}
    return {"hookSpecificOutput": {"updatedToolOutput": sanitized}}


class FlightBookingOutput(BaseModel):
    flight_id: str
    passenger_name: str
    price_usd: float

    @field_validator("price_usd")
    @classmethod
    def price_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError(f"price_usd must be positive, got {value}")
        return value


async def _last_output(client: ClaudeSDKClient, prompt: str) -> object:
    await client.query(prompt)
    last: object = ""
    async for message in client.receive_response():
        if hasattr(message, "output"):
            last = message.output
        elif hasattr(message, "result"):
            last = message.result
    return last


async def run_with_validation_retry(
    client: ClaudeSDKClient,
    prompt: str,
    validator: Callable[[object], object],
    model: str = PRIMARY_MODEL,
    is_fallback: bool = False,
) -> object:
    last_output: object = None
    last_error: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        if last_error:
            current_prompt = (
                f"{prompt}\n\nCorrection {attempt}/{MAX_RETRIES}: "
                f"{last_error}"
            )
        else:
            current_prompt = prompt
        client.options = ClaudeAgentOptions(model=model)
        result_output = await _last_output(client, current_prompt)
        try:
            return validator(result_output)
        except ValueError as exc:
            last_output = result_output
            last_error = str(exc)
    if not is_fallback:
        return await run_with_validation_retry(
            client,
            prompt,
            validator,
            model=FALLBACK_MODEL,
            is_fallback=True,
        )
    raise RuntimeError(
        f"Validation failed after {MAX_RETRIES} retries on both "
        f"{PRIMARY_MODEL} and {FALLBACK_MODEL}. "
        f"Last error: {last_error}. Last output: {last_output}"
    )


options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    allowed_tools=["book_flight", "issue_refund"],
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher="book_flight|issue_refund",
                hooks=[enforce_refund_cap],
            )
        ],
        "PostToolUse": [
            HookMatcher(matcher=".*", hooks=[sanitize_tool_output])
        ],
    },
    max_budget_usd=5.0,
)


async def run_booking_step(client: ClaudeSDKClient, prompt: str):
    await client.query(prompt)
    async for message in client.receive_response():
        if hasattr(message, "tool_calls"):
            for call in message.tool_calls:
                try:
                    FlightBookingOutput.model_validate(call.output)
                except ValueError:
                    return await run_with_validation_retry(
                        client,
                        prompt,
                        FlightBookingOutput.model_validate,
                    )
    return None


def main() -> None:
    class _Call:
        def __init__(self, output: dict) -> None:
            self.output = output

    class _Msg:
        def __init__(self, calls: list) -> None:
            self.tool_calls = calls

    class _Client:
        async def query(
            self, prompt: str, session_id: str = "default"
        ) -> None:
            return None

        async def receive_response(self):
            yield _Msg(
                [
                    _Call(
                        {
                            "flight_id": "AA100",
                            "passenger_name": "Ada",
                            "price_usd": 200.0,
                        }
                    )
                ]
            )

    asyncio.run(run_booking_step(_Client(), "book AA100"))
    print("booked AA100")


if __name__ == "__main__":
    main()
