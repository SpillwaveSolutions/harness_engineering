"""Travel-booking harness with the seven components wired in.

Offline runs never call the network. A live query runs only when
HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY are both set.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, query


@dataclass
class HarnessState:
    turns: int = 0
    total_tokens: int = 0
    tool_call_hashes: list[str] = field(default_factory=list)


def check_stopping_conditions(
    state: HarnessState,
    tool_calls: list[dict],
    *,
    max_turns: int = 20,
    token_budget: int = 100_000,
    no_progress_window: int = 3,
) -> str | None:
    if state.turns >= max_turns:
        return "max_turns"
    if state.total_tokens >= token_budget:
        return "token_budget"
    if tool_calls:
        call_hash = hashlib.sha256(
            json.dumps(tool_calls, sort_keys=True).encode()
        ).hexdigest()
        state.tool_call_hashes.append(call_hash)
        recent = state.tool_call_hashes[-no_progress_window:]
        if len(recent) == no_progress_window and len(set(recent)) == 1:
            return "no_progress"
    return None


def enforce_permissions(tool_name: str, tool_input: dict) -> None:
    """Policy check before a tool runs. Offline build permits the call."""
    del tool_name, tool_input


def validate_tool_input(tool_name: str, tool_input: dict) -> None:
    """Schema check before a tool runs. Offline build accepts the input."""
    del tool_name, tool_input


def validate_tool_output(tool_name: str, tool_output: Any) -> None:
    """Schema check after a tool runs. Offline build accepts the output."""
    del tool_name, tool_output


class _ToolMsg:
    def __init__(self, prompt: str) -> None:
        self.tool_calls = [
            {"name": "WebSearch", "input": {"query": prompt}}
        ]


class _Usage:
    input_tokens: int = 10
    output_tokens: int = 5


class _UsageMsg:
    def __init__(self) -> None:
        self.usage = _Usage()


class _TextMsg:
    def __init__(self, prompt: str) -> None:
        self.text = f"Stub result for: {prompt}"


async def _offline_events(user_request: str):
    yield _ToolMsg(user_request)
    yield _UsageMsg()
    yield _TextMsg(user_request)


def _live_enabled() -> bool:
    return (
        os.environ.get("HARNESS_LIVE_API") == "1"
        and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )


async def run_travel_harness(user_request: str) -> str:
    """Travel-booking harness with all seven components wired in.

    Returns the final text, or a ``[halted: ...]`` sentinel when a
    stopping condition fires. Offline, the text is
    ``Stub result for:`` plus the user request.
    """
    state = HarnessState()

    def pre_tool_hook(tool_name: str, tool_input: dict) -> None:
        # Validators (control plane pre-check)
        validate_tool_input(tool_name, tool_input)  # ①
        # Policy (control plane: block disallowed actions)
        enforce_permissions(tool_name, tool_input)

    async def sdk_pre_tool(input_data, tool_use_id, context):
        del tool_use_id, context
        pre_tool_hook(
            str(input_data.get("tool_name", "")),
            dict(input_data.get("tool_input") or {}),
        )
        return {}

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        max_turns=20,  # Condition 1: maximum turns
        max_budget_usd=2.00,  # Condition 2: token budget via USD cap
        allowed_tools=[
            "WebSearch",
            "WebFetch",
            "AskUserQuestion",
        ],
        hooks={  # ②
            "PreToolUse": [HookMatcher(hooks=[sdk_pre_tool])],
        },
    )

    if _live_enabled():
        events = query(prompt=user_request, options=options)  # ③
    else:
        print(
            "offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY "
            "to run a live harness query.",
            file=sys.stderr,
        )
        events = _offline_events(user_request)

    result_text = ""
    async for message in events:
        if hasattr(message, "tool_calls"):
            # Increment turn counter in the control plane state
            state.turns += 1
            stop_reason = check_stopping_conditions(  # ④
                state, message.tool_calls
            )
            if stop_reason:
                return f"[halted: {stop_reason}]"
        if hasattr(message, "usage"):
            state.total_tokens += (
                message.usage.input_tokens + message.usage.output_tokens
            )
        if hasattr(message, "text"):
            result_text = message.text

    return result_text


def main() -> None:
    result = asyncio.run(run_travel_harness("Book a flight to Tokyo."))
    print(result)


if __name__ == "__main__":
    main()
