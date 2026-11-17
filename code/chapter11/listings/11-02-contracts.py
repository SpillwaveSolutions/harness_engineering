from dataclasses import dataclass
from typing import Literal


@dataclass
class ProposedAction:
    tool_name: str          # "book_flight"
    tool_input: dict        # {"fare_id": ..., "cabin": "business"}
    generator_rationale: str  # why generator chose this action

@dataclass
class CritiqueResult:
    objection: str          # human-readable challenge, grounded in rubric
    confidence_floor_met: bool  # True if critic confidence >= 0.65
    confidence_score: float  # 0.0-1.0: critic certainty the plan is right
    rubric_scores: dict     # per-criterion scores from the red-team rubric

@dataclass
class ArbitrationDecision:
    decision: Literal["proceed", "amend", "escalate", "default_deny"]
    rationale: str
    amended_input: dict | None  # populated when decision == "amend"
