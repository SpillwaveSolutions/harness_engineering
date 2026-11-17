import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

import anthropic


@dataclass
class MemoryEntry:
    content: str
    importance: float          # 0.0-1.0, rated at write time
    created_at: datetime
    use_successes: int = 0
    use_failures: int = 0

    def recency_score(self, decay: float = 0.995, interval_hours: float = 1.0) -> float:
        elapsed = datetime.now(UTC) - self.created_at
        age_hours = elapsed.total_seconds() / 3600
        intervals = age_hours / interval_hours
        return math.pow(decay, intervals)  # ① exponential decay per Park et al.

    def memory_worth(self) -> float:
        """Simsek 2026 two-counter outcome signal."""
        total = self.use_successes + self.use_failures
        if total == 0:
            return 0.5  # uninformed prior
        return self.use_successes / total  # ② converges to P(success | retrieved)

def saliency_score(entry: MemoryEntry, relevance: float) -> float:
    """Composite score: recency + importance + relevance, equal weights."""
    return (entry.recency_score() + entry.importance + relevance) / 3.0  # ③

def rate_importance(content: str) -> float:
    """Ask the model to rate poignancy at write time."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; returning offline importance 0.5",
            file=sys.stderr,
        )
        return 0.5
    client = anthropic.Anthropic()
    prompt = (
        "On a scale of 1 to 10, where 1 is purely mundane and 10 is extremely "
        f"poignant or consequential, rate this memory:\n\n{content}\n\nRespond with "
        "only an integer."
    )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    return min(max(int(raw), 1), 10) / 10.0  # ④ normalize to [0, 1]

def should_evict(entry: MemoryEntry, threshold: float = 0.15) -> bool:
    """Evict when saliency and Memory Worth are both under the threshold."""
    low_saliency = saliency_score(entry, relevance=0.0) < threshold
    low_worth = entry.memory_worth() < threshold
    return low_saliency and low_worth  # ⑤ both signals agree before evicting


def main() -> None:
    entry = MemoryEntry(
        content="aisle seat",
        importance=0.5,
        created_at=datetime.now(UTC),
    )
    print(f"{entry.memory_worth():.1f}")
    print(f"{rate_importance(entry.content):.1f}")


if __name__ == "__main__":
    main()
