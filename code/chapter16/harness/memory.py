"""Stub MemorySubsystem for chapter 16 listings.

Self-contained in-memory implementation that satisfies the
interface expected by listing 16-01.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MemoryEntry:
    content: str
    namespace: str


class MemorySubsystem:
    """Minimal in-memory store used by listing 16-01 tests."""

    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._store: list[MemoryEntry] = []

    def write(self, content: str) -> None:
        """Write content to in-memory store."""
        self._store.append(
            MemoryEntry(content=content, namespace=self.namespace)
        )

    def search(
        self, query: str, top_k: int = 5
    ) -> list[MemoryEntry]:
        """Return entries whose content contains query substring."""
        matches = [
            e for e in self._store if query.lower() in e.content.lower()
        ]
        return matches[:top_k]
