"""Extract facts from a turn and search them later.

When OPENAI_API_KEY is unset, get_memory() returns an in-memory fake.
When ANTHROPIC_API_KEY is unset, the model call is skipped.
"""

from __future__ import annotations

import os
import sys

import anthropic
from mem0 import Memory

# Mem0's default Memory() passes max_tokens to OpenAI. Pin a chat
# model that still accepts max_tokens, plus an explicit embedder.
MEM0_CONFIG = {
    "llm": {
        "provider": "openai",
        "config": {"model": "gpt-4.1-mini", "max_tokens": 1024},
    },
    "embedder": {
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
}

_OFFLINE_NOTE = "offline: noted the user turn"


class _InMemoryMemory:
    """Small stand-in with the add/search shape the listing uses."""

    def __init__(self) -> None:
        self._by_user: dict[str, list[dict[str, str]]] = {}

    def add(
        self,
        messages: list[dict],
        user_id: str | None = None,
        **_kwargs: object,
    ) -> dict:
        key = user_id or ""
        stored = self._by_user.setdefault(key, [])
        seen = {item["memory"] for item in stored}
        added: list[dict[str, str]] = []
        for message in messages:
            content = message.get("content", "")
            if (
                isinstance(content, str)
                and content
                and content not in seen
            ):
                seen.add(content)
                added.append({"memory": content})
        stored.extend(added)
        return {"results": added}

    def search(
        self,
        query: str,
        filters: dict | None = None,
        limit: int = 5,
        **_kwargs: object,
    ) -> dict:
        key = str((filters or {}).get("user_id", ""))
        hits = self._by_user.get(key, [])
        if query:
            needle = query.lower()
            hits = [hit for hit in hits if needle in hit["memory"].lower()]
        return {"results": hits[:limit]}


_MEMORY: _InMemoryMemory | None = None


def get_memory() -> _InMemoryMemory | Memory:
    """One Mem0 or stand-in instance for the process."""
    global _MEMORY
    if _MEMORY is not None:
        return _MEMORY
    if os.environ.get("OPENAI_API_KEY"):
        _MEMORY = Memory.from_config(MEM0_CONFIG)
    else:
        print(
            "OPENAI_API_KEY unset; using in-memory memory",
            file=sys.stderr,
        )
        _MEMORY = _InMemoryMemory()
    return _MEMORY


def process_turn_and_extract(
    user_id: str, messages: list[dict]
) -> list[dict]:
    """Run a model call and store extracted facts from the response."""
    memory = get_memory()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline extraction",
            file=sys.stderr,
        )
        assistant_text = _OFFLINE_NOTE
    else:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=messages,
        )
        assistant_text = response.content[0].text

    full_turn = messages + [
        {"role": "assistant", "content": assistant_text}
    ]
    result = memory.add(full_turn, user_id=user_id)
    return result.get("results", [])


def retrieve_facts_for_session(
    user_id: str, query: str, top_k: int = 5
) -> list[str]:
    """Retrieve the most relevant extracted facts before the next model call."""
    memory = get_memory()
    # Mem0 requires filters={...} for entity scoping in search.
    results = memory.search(
        query, filters={"user_id": user_id}, limit=top_k
    )
    return [row["memory"] for row in results.get("results", [])]


def main() -> None:
    user_id = "demo-user"
    stored = process_turn_and_extract(
        user_id,
        [{"role": "user", "content": "I prefer aisle seats."}],
    )
    found = retrieve_facts_for_session(user_id, "aisle", top_k=5)
    print(stored)
    print(found)


if __name__ == "__main__":
    main()
