"""Tests for listing 06-06-saliency-eviction.

Pure logic tests for MemoryEntry.recency_score, .memory_worth,
saliency_score, and should_evict. The rate_importance helper hits the
Anthropic API and is gated on ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest


def _make_entry(
    m,
    *,
    content: str = "x",
    importance: float = 0.5,
    age_hours: float = 0.0,
    successes: int = 0,
    failures: int = 0,
):
    return m.MemoryEntry(
        content=content,
        importance=importance,
        created_at=datetime.now(UTC) - timedelta(hours=age_hours),
        use_successes=successes,
        use_failures=failures,
    )


def test_recency_score_is_one_for_brand_new_entry(load_listing) -> None:
    m = load_listing("06-06-saliency-eviction")
    e = _make_entry(m, age_hours=0.0)
    assert e.recency_score() == pytest.approx(1.0, rel=1e-3)


def test_recency_score_decays_exponentially_with_age(load_listing) -> None:
    """0.995^100 ≈ 0.605 — verifies the Park et al. decay constant."""
    m = load_listing("06-06-saliency-eviction")
    fresh = _make_entry(m, age_hours=0.0).recency_score()
    aged = _make_entry(m, age_hours=100.0).recency_score()
    assert fresh > aged
    assert aged == pytest.approx(0.605, rel=0.05)


def test_memory_worth_uninformed_prior_is_half(load_listing) -> None:
    m = load_listing("06-06-saliency-eviction")
    e = _make_entry(m, successes=0, failures=0)
    assert e.memory_worth() == 0.5


def test_memory_worth_converges_to_success_rate(load_listing) -> None:
    m = load_listing("06-06-saliency-eviction")
    e = _make_entry(m, successes=8, failures=2)
    assert e.memory_worth() == pytest.approx(0.8)


def test_saliency_score_equal_weighting(load_listing) -> None:
    """score = (recency + importance + relevance) / 3."""
    m = load_listing("06-06-saliency-eviction")
    e = _make_entry(m, importance=0.6, age_hours=0.0)
    expected = (1.0 + 0.6 + 0.3) / 3.0
    assert m.saliency_score(e, relevance=0.3) == pytest.approx(expected, rel=1e-3)


def test_should_evict_requires_both_signals_below_threshold(load_listing) -> None:
    """Stale entry (low recency, low importance, low MW) evicts; specialist
    entry (low recency but high MW) is kept; recent entry is kept regardless."""
    m = load_listing("06-06-saliency-eviction")
    stale = _make_entry(
        m, importance=0.05, age_hours=2000.0, successes=1, failures=99
    )
    assert m.should_evict(stale, threshold=0.15) is True

    specialist = _make_entry(
        m, importance=0.05, age_hours=2000.0, successes=99, failures=1
    )
    assert m.should_evict(specialist, threshold=0.15) is False

    fresh = _make_entry(
        m, importance=0.05, age_hours=0.0, successes=0, failures=10
    )
    assert m.should_evict(fresh, threshold=0.15) is False


def test_rate_importance_offline_is_one_half(
    load_listing, monkeypatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("06-06-saliency-eviction")
    score = module.rate_importance("moving to Tokyo next month")
    assert score == 0.5


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_rate_importance_returns_normalized_score(load_listing) -> None:
    """rate_importance hits claude-sonnet-4-6 and returns a [0, 1] float."""
    m = load_listing("06-06-saliency-eviction")
    score = m.rate_importance(
        "User said they will be moving to Tokyo next month for cancer treatment."
    )
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
