"""Tests for listing 12-13-provenance.

Three Pydantic v2 models: ClaimSourceMapping, SubagentArtifact,
SynthesisResult. Load-bearing claims from §12.13:

1. ClaimSourceMapping has seven required fields: claim, source_url,
   source_name, retrieved_at, excerpt, confidence (float 0.0–1.0),
   methodology.
2. SubagentArtifact aggregates a list of ClaimSourceMapping items and
   a coverage_gaps list — structured output, not free-form strings.
3. SynthesisResult preserves conflicts and coverage_gaps rather than
   discarding them; provenance is a full list of ClaimSourceMapping.
4. Pydantic raises ValidationError for wrong types (e.g., str where
   float is expected for confidence).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def provenance_module(load_listing):
    return load_listing("12-13-provenance")


@pytest.fixture
def ClaimSourceMapping(provenance_module):
    return provenance_module.ClaimSourceMapping


@pytest.fixture
def SubagentArtifact(provenance_module):
    return provenance_module.SubagentArtifact


@pytest.fixture
def SynthesisResult(provenance_module):
    return provenance_module.SynthesisResult


@pytest.fixture
def sample_claim(ClaimSourceMapping):
    return ClaimSourceMapping(
        claim="The Marriott Bonvoy program offers 10 points per dollar.",
        source_url="https://www.marriott.com/loyalty/terms/default.mi",
        source_name="Marriott International",
        retrieved_at="2026-05-25T00:00:00Z",
        excerpt="Members earn 10 Base Points per dollar spent.",
        confidence=0.95,
        methodology="Direct extraction from official T&C page.",
    )


# --- ClaimSourceMapping ---

def test_claim_source_mapping_fields(sample_claim):
    assert sample_claim.claim.startswith("The Marriott")
    assert sample_claim.source_url.startswith("https://")
    assert sample_claim.source_name == "Marriott International"
    assert "T00:00:00Z" in sample_claim.retrieved_at
    assert len(sample_claim.excerpt) > 0
    assert 0.0 <= sample_claim.confidence <= 1.0
    assert len(sample_claim.methodology) > 0


def test_claim_source_mapping_confidence_is_float(sample_claim):
    assert isinstance(sample_claim.confidence, float)


def test_claim_source_mapping_rejects_bad_confidence_type(ClaimSourceMapping):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ClaimSourceMapping(
            claim="test",
            source_url="https://example.com",
            source_name="Example",
            retrieved_at="2026-05-25T00:00:00Z",
            excerpt="test excerpt",
            confidence="not-a-float",   # wrong type
            methodology="test",
        )


def test_claim_source_mapping_is_pydantic_model(ClaimSourceMapping):
    from pydantic import BaseModel
    assert issubclass(ClaimSourceMapping, BaseModel)


def test_claim_source_mapping_has_seven_fields(ClaimSourceMapping):
    fields = ClaimSourceMapping.model_fields
    assert len(fields) == 7
    expected = {
        "claim", "source_url", "source_name", "retrieved_at",
        "excerpt", "confidence", "methodology",
    }
    assert set(fields.keys()) == expected


# --- SubagentArtifact ---

def test_subagent_artifact_happy_path(SubagentArtifact, sample_claim):
    artifact = SubagentArtifact(
        agent_id="hotel-loyalty-agent-v1",
        task_id="task-abc123",
        claims=[sample_claim],
        coverage_gaps=["Redemption rates for partner hotels not available."],
    )
    assert artifact.agent_id == "hotel-loyalty-agent-v1"
    assert artifact.task_id == "task-abc123"
    assert len(artifact.claims) == 1
    assert artifact.claims[0].confidence == 0.95
    assert len(artifact.coverage_gaps) == 1


def test_subagent_artifact_empty_claims_allowed(SubagentArtifact):
    artifact = SubagentArtifact(
        agent_id="agent-x",
        task_id="task-empty",
        claims=[],
        coverage_gaps=[],
    )
    assert artifact.claims == []
    assert artifact.coverage_gaps == []


def test_subagent_artifact_rejects_missing_agent_id(SubagentArtifact):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SubagentArtifact(
            task_id="task-xyz",
            claims=[],
            coverage_gaps=[],
        )


# --- SynthesisResult ---

def test_synthesis_result_preserves_conflicts(
    SynthesisResult, sample_claim
):
    result = SynthesisResult(
        recommended_option={"hotel": "Marriott NYC", "rate": "prepaid"},
        all_options=[
            {"hotel": "Marriott NYC", "rate": "prepaid"},
            {"hotel": "Hilton Midtown", "rate": "flexible"},
        ],
        conflicts=[
            {
                "field": "loyalty_points",
                "agent_a": "18000",
                "agent_b": "20000",
                "resolution": "deferred to human review",
            }
        ],
        coverage_gaps=["Business-class upgrade availability unknown."],
        provenance=[sample_claim],
    )
    assert len(result.conflicts) == 1
    assert result.conflicts[0]["field"] == "loyalty_points"
    assert len(result.coverage_gaps) == 1
    assert len(result.provenance) == 1


def test_synthesis_result_empty_conflicts_and_gaps(SynthesisResult):
    result = SynthesisResult(
        recommended_option={"hotel": "Marriott"},
        all_options=[{"hotel": "Marriott"}],
        conflicts=[],
        coverage_gaps=[],
        provenance=[],
    )
    assert result.conflicts == []
    assert result.coverage_gaps == []
    assert result.provenance == []


def test_synthesis_result_is_pydantic_model(SynthesisResult):
    from pydantic import BaseModel
    assert issubclass(SynthesisResult, BaseModel)


def test_synthesis_result_has_five_fields(SynthesisResult):
    fields = SynthesisResult.model_fields
    expected = {
        "recommended_option", "all_options", "conflicts",
        "coverage_gaps", "provenance",
    }
    assert set(fields.keys()) == expected
