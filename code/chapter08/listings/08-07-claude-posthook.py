"""Mask card numbers and SSNs in tool output."""

from __future__ import annotations

import asyncio
import re
from types import SimpleNamespace

from claude_agent_sdk import PostToolUseHookInput

PAN_PATTERN = re.compile(r"\b(\d{6})\d{6,9}(\d{4})\b")
SSN_PATTERN = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")


async def sanitize_tool_output(
    input_data: PostToolUseHookInput,
    tool_use_id: str,
    context,
) -> dict:
    if not isinstance(input_data.tool_response, str):
        return {}
    sanitized = input_data.tool_response
    sanitized = PAN_PATTERN.sub(r"\1××××××\2", sanitized)
    sanitized = SSN_PATTERN.sub("[SSN REDACTED]", sanitized)
    if sanitized == input_data.tool_response:
        return {}
    return {"hookSpecificOutput": {"updatedToolOutput": sanitized}}


def main() -> None:
    data = SimpleNamespace(
        tool_response="card 4111111111111111 ssn 123-45-6789"
    )
    result = asyncio.run(sanitize_tool_output(data, "demo", None))
    print(result["hookSpecificOutput"]["updatedToolOutput"])


if __name__ == "__main__":
    main()
