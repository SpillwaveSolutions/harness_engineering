"""Spend ceiling and a tool that is always off."""

from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    max_budget_usd=50.0,
    disallowed_tools=["delete_booking"],
)


def main() -> None:
    print(options.max_budget_usd)
    print(options.disallowed_tools[0])


if __name__ == "__main__":
    main()
