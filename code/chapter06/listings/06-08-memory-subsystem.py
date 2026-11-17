"""Mem0 wrapper with provenance tags and an append-only audit log.

OPENAI_API_KEY selects real Mem0. Without it, get_memory() returns
an in-memory fake so write/read/inspect stay deterministic.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from mem0 import Memory

AUDIT_LOG = Path("./memory_audit.jsonl")

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


class _InMemoryMemory:
    """add/search/get_all stand-in used when no API key is configured."""

    def __init__(self) -> None:
        self._by_user: dict[str, list[dict[str, str]]] = {}

    def add(
        self,
        messages: list[dict],
        user_id: str | None = None,
        **_kwargs: object,
    ) -> dict:
        key = user_id or ""
        entries: list[dict[str, str]] = []
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str) and content:
                entries.append({"memory": content})
        self._by_user.setdefault(key, []).extend(entries)
        return {"results": entries}

    def search(
        self,
        query: str,
        filters: dict | None = None,
        limit: int = 5,
        **_kwargs: object,
    ) -> dict:
        key = str((filters or {}).get("user_id", ""))
        hits = self._by_user.get(key, [])
        tokens = {tok.lower() for tok in query.split() if tok}
        if tokens:
            hits = [
                hit
                for hit in hits
                if tokens & set(hit["memory"].lower().split())
            ]
        return {"results": hits[:limit]}

    def get_all(
        self, filters: dict | None = None, **_kwargs: object
    ) -> dict:
        key = str((filters or {}).get("user_id", ""))
        return {"results": list(self._by_user.get(key, []))}


def get_memory() -> _InMemoryMemory | Memory:
    """Real Mem0 when OPENAI_API_KEY is set, otherwise a fresh fake."""
    if os.environ.get("OPENAI_API_KEY"):
        return Memory.from_config(MEM0_CONFIG)
    print(
        "OPENAI_API_KEY unset; using in-memory memory",
        file=sys.stderr,
    )
    return _InMemoryMemory()


@dataclass
class ProvenanceEnvelope:
    session_id: str
    timestamp: str
    trust_score: float
    source_channel: str
    entry_content: str


class InspectableMemorySubsystem:
    """Wraps Mem0 with provenance tagging and an append-only audit log."""

    def __init__(self, user_id: str, session_id: str | None = None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self._mem = get_memory()

    def write(
        self,
        messages: list[dict],
        trust_score: float = 0.8,
        source_channel: str = "user_input",
    ) -> list[dict]:
        """Extract facts from messages and store with provenance."""
        results = self._mem.add(messages, user_id=self.user_id)
        for entry in results.get("results", []):
            envelope = ProvenanceEnvelope(
                session_id=self.session_id,
                timestamp=datetime.now(UTC).isoformat(),
                trust_score=trust_score,
                source_channel=source_channel,
                entry_content=entry.get("memory", ""),
            )
            self._append_audit({"op": "write", **asdict(envelope)})
        return results.get("results", [])

    def read(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve facts and log the read operation."""
        results = self._mem.search(
            query, filters={"user_id": self.user_id}, limit=top_k
        )
        memories = [row["memory"] for row in results.get("results", [])]
        self._append_audit(
            {
                "op": "read",
                "session_id": self.session_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "query": query,
                "retrieved_count": len(memories),
            }
        )
        return memories

    def inspect(self) -> list[dict]:
        """Return all memory entries for this user."""
        results = self._mem.get_all(filters={"user_id": self.user_id})
        return results.get("results", [])

    def audit_log(self, limit: int = 100) -> list[dict]:
        """Return recent write and read operations from the append-only log."""
        if not AUDIT_LOG.exists():
            return []
        lines = AUDIT_LOG.read_text().strip().splitlines()
        return [json.loads(line) for line in lines[-limit:]]

    def _append_audit(self, record: dict) -> None:
        with AUDIT_LOG.open("a") as handle:
            handle.write(json.dumps(record) + "\n")


def main() -> None:
    import tempfile

    global AUDIT_LOG
    AUDIT_LOG = Path(tempfile.mkdtemp()) / "memory_audit.jsonl"
    subsystem = InspectableMemorySubsystem("demo-user", session_id="demo")
    stored = subsystem.write(
        [{"role": "user", "content": "allergic to shellfish"}]
    )
    print(stored[0]["memory"])
    print(subsystem.read("shellfish"))


if __name__ == "__main__":
    main()
