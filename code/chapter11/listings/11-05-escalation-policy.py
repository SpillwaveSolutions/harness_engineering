from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CONFIDENCE_FLOOR = 0.65
CONFIDENCE_DELTA_THRESHOLD = 0.20
MAX_AMEND_ROUNDS = 2


@dataclass
class ProposedAction:
    """Minimal action the policy reads. `decide` uses `tool_name`."""

    tool_name: str
    confidence_floor_met: bool = False
    confidence_score: float = 0.0


@dataclass
class CritiqueResult:
    """Minimal critique. `decide` uses the confidence fields."""

    tool_name: str
    confidence_floor_met: bool
    confidence_score: float


@dataclass
class EscalationPolicy:
    irreversible_tools: set[str]  # {"book_flight", "cancel_booking", ...}

    def decide(
        self,
        proposed: ProposedAction,
        critique: CritiqueResult,
        round_number: int,
    ) -> Literal["proceed", "amend", "escalate", "default_deny"]:
        is_irreversible = proposed.tool_name in self.irreversible_tools

        # Category-level constraint: irreversible always escalates
        if is_irreversible:
            if not critique.confidence_floor_met:
                return "default_deny"
            return "escalate"

        # Reversible + below confidence floor -> escalate
        if not critique.confidence_floor_met:
            return "escalate"

        # Reversible + large delta + rounds remaining -> amend
        delta = 1.0 - critique.confidence_score
        large_delta = delta > CONFIDENCE_DELTA_THRESHOLD
        rounds_left = round_number < MAX_AMEND_ROUNDS
        if large_delta and rounds_left:
            return "amend"

        # Reversible + small delta or rounds exhausted -> proceed
        return "proceed"


def main() -> int:
    policy = EscalationPolicy(irreversible_tools={"book_flight"})
    decision = policy.decide(
        ProposedAction(tool_name="book_flight"),
        CritiqueResult(
            tool_name="book_flight",
            confidence_floor_met=True,
            confidence_score=0.9,
        ),
        round_number=0,
    )
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
