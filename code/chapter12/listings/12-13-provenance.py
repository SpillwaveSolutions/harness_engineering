
from pydantic import BaseModel


class ClaimSourceMapping(BaseModel):
    """Structured provenance unit that every subagent must return."""
    claim: str                      # the factual assertion
    source_url: str                 # canonical source URI
    source_name: str                # organization or publication name
    retrieved_at: str               # ISO 8601 timestamp
    excerpt: str                    # verbatim supporting passage
    confidence: float               # 0.0–1.0
    methodology: str                # how the claim was established

class SubagentArtifact(BaseModel):
    agent_id: str
    task_id: str
    claims: list[ClaimSourceMapping]  # structured, not free-form
    coverage_gaps: list[str]          # what this agent could not determine

class SynthesisResult(BaseModel):
    recommended_option: dict
    all_options: list[dict]
    conflicts: list[dict]           # preserved, not discarded
    coverage_gaps: list[str]        # preserved, not discarded
    provenance: list[ClaimSourceMapping]  # full claim-to-source mapping
