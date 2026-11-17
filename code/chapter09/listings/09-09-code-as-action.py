"""Ask for a migration script. Offline, return a one-line summary."""

from __future__ import annotations

import os
import sys

import anthropic

OFFLINE_SUMMARY = "offline: transferred 0 records (0 success, 0 errors)"

_SYSTEM = """You are a travel data migration agent.
When asked to transfer booking data, write a Python script that:
1. Reads from the source (a sheet tool on disk)
2. Transforms records to the target schema
3. Writes to the destination (a CRM tool on disk)
4. Returns only a summary: total records, success count, error count.
Intermediate row data must NOT be returned to context.
"""


def run_code_as_action(task: str) -> str:
    """Return a one-line summary. Call the model only when a key is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline summary",
            file=sys.stderr,
        )
        return OFFLINE_SUMMARY
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


def main() -> None:
    print(
        run_code_as_action(
            "Transfer all completed bookings from the Q3 sheet. "
            "Report totals only."
        )
    )


if __name__ == "__main__":
    main()
