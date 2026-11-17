"""Deny a refund that exceeds the cap before the tool runs."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    PreToolUseHookInput,
)

REFUND_CAP_USD = 500.0


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
                    f"${REFUND_CAP_USD:.2f} cap. "
                    "Escalate to a manager for approval."
                ),
            }
        }
    return {}


options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(
                matcher="issue_refund", hooks=[enforce_refund_cap]
            )
        ]
    }
)


def main() -> None:
    data = SimpleNamespace(
        tool_name="issue_refund", tool_input={"amount": 900}
    )
    result = asyncio.run(enforce_refund_cap(data, "demo", None))
    decision = result["hookSpecificOutput"]["permissionDecision"]
    print(decision)


if __name__ == "__main__":
    main()
