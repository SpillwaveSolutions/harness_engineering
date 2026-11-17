"""Persistent fact block and turn extraction.

Importing this file does not build a client and does not need
ANTHROPIC_API_KEY. Offline extraction reads dates and amounts from
the message text. A live model call runs only when HARNESS_LIVE_API=1
and ANTHROPIC_API_KEY are both set.
"""

from __future__ import annotations

import os
import re
import sys

import anthropic


# A persistent fact-extraction block: lives OUTSIDE the rolling history.
# The harness re-injects this verbatim at the top of every payload.
class PersistentFactBlock:
    def __init__(self) -> None:
        self._facts: dict[str, str] = {}

    def update(self, key: str, value: str) -> None:
        """Write a fact. Precise values only; no paraphrase."""
        self._facts[key] = value

    def to_context_segment(self) -> str:
        """Render the fact block for injection into the system prompt."""
        if not self._facts:
            return ""
        lines = ["PERSISTENT FACTS (do not paraphrase, do not compress):"]
        for k, v in self._facts.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)


# The extraction model returns facts by calling this tool. Forcing
# tool_choice guarantees a structured tool_use block: there is no
# JSON string to parse and no markdown fence to strip.
RECORD_FACTS_TOOL = {
    "name": "record_facts",
    "description": (
        "Record dates, numeric values, and explicit commitments "
        "found in the user message as key-value pairs."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": {"type": "string"},
    },
}

_FACT_PATTERN = re.compile(
    r"("
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|(?:\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},\s+\d{4})"
    r"|\$\d+(?:,\d{3})*(?:\.\d+)?"
    r")",
    re.IGNORECASE,
)


def _facts_from_text(turn_text: str) -> list[dict[str, str]]:
    """Pull dates and dollar amounts out of the message, in order."""
    facts: list[dict[str, str]] = []
    date_n = 0
    amount_n = 0
    for match in _FACT_PATTERN.finditer(turn_text):
        value = match.group(0)
        if value.startswith("$"):
            amount_n += 1
            key = "amount" if amount_n == 1 else f"amount_{amount_n}"
        else:
            date_n += 1
            key = "date" if date_n == 1 else f"date_{date_n}"
        facts.append({key: value})
    return facts


def _store(
    facts: list[dict[str, str]], fact_block: PersistentFactBlock
) -> list[dict[str, str]]:
    for fact in facts:
        for key, value in fact.items():
            fact_block.update(key, value)
    return facts


def _live_enabled(client: anthropic.Anthropic | None) -> bool:
    return (
        client is not None
        and os.environ.get("HARNESS_LIVE_API") == "1"
        and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )


def _extract_live(
    client: anthropic.Anthropic,
    turn_text: str,
    fact_block: PersistentFactBlock,
) -> list[dict[str, str]]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=(
            "Extract ONLY dates, numeric values, and explicit "
            "commitments from the user message. Record each one by "
            "calling record_facts with semantic keys. If there are "
            "none, call record_facts with an empty object."
        ),
        tools=[RECORD_FACTS_TOOL],
        tool_choice={"type": "tool", "name": "record_facts"},
        messages=[{"role": "user", "content": turn_text}],
    )
    # A forced tool_choice yields exactly one tool_use block; the loop
    # is defensive. block.input is already a parsed dict.
    found: list[dict[str, str]] = []
    for block in response.content:
        if block.type == "tool_use":
            for key, value in block.input.items():
                text = str(value)
                fact_block.update(key, text)
                found.append({key: text})
    return found


def extract_facts_from_turn(
    client: anthropic.Anthropic | None,
    turn_text: str,
    fact_block: PersistentFactBlock,
) -> list[dict[str, str]]:
    """Record dates, amounts, and commitments from this turn.

    Returns the list of fact dicts written into the block. Offline,
    those dicts are derived from the message text.
    """
    if _live_enabled(client):
        return _extract_live(client, turn_text, fact_block)
    print(
        "offline: set HARNESS_LIVE_API=1 and ANTHROPIC_API_KEY "
        "to extract facts with the model.",
        file=sys.stderr,
    )
    return _store(_facts_from_text(turn_text), fact_block)


def main() -> None:
    block = PersistentFactBlock()
    text = (
        "I need to return my order by June 15, 2026. "
        "The total was $127.50."
    )
    facts = extract_facts_from_turn(None, text, block)
    print(facts)
    print(block.to_context_segment())


if __name__ == "__main__":
    main()
