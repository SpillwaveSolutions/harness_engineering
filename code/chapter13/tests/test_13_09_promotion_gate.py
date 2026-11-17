"""Tests for listing 13-09-promotion-gate (§13.9).

Verifies that:
  - run_promotion_gate returns True when all metrics are above floor and within
    the regression limit.
  - run_promotion_gate returns False when any metric is below the absolute floor.
  - run_promotion_gate returns False when any metric exceeds the max_regression
    limit even while remaining above the floor.
  - The listing imports (or stubs) score_booking_response without NameError.
  - THRESHOLDS dict has the three expected keys.

These tests mock the langsmith Client to avoid live network calls.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_gate_module():
    """Load 13-09-promotion-gate.py with langsmith patched out."""
    langsmith_mock = MagicMock()
    langsmith_client_mock = MagicMock()
    langsmith_mock.Client.return_value = langsmith_client_mock

    with patch.dict(sys.modules, {"langsmith": langsmith_mock}):
        path = LISTINGS_DIR / "13-09-promotion-gate.py"
        if not path.exists():
            pytest.fail(f"listing not found at {path}")
        spec = importlib.util.spec_from_file_location("listing_13_09", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_13_09"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod, langsmith_client_mock


def test_module_imports_without_nameerror():
    """§13.9: the module must import without NameError for score_booking_response."""
    mod, _ = _load_gate_module()
    assert hasattr(mod, "score_booking_response"), (
        "score_booking_response must be defined (imported from 13-08 or stubbed)"
    )


def test_thresholds_has_three_keys():
    """§13.9: THRESHOLDS covers booking_quality, no_hallucination, tool_call_correct."""
    mod, _ = _load_gate_module()
    assert set(mod.THRESHOLDS.keys()) == {
        "booking_quality",
        "no_hallucination",
        "tool_call_correct",
    }


def _make_pandas_mock(scores: dict[str, float]):
    """Return a mock result whose .to_pandas()[metric].mean() returns scores[metric]."""
    import pandas as pd  # available through langsmith transitive dep; safe to skip if absent
    df = pd.DataFrame({k: [v] for k, v in scores.items()})

    result_mock = MagicMock()
    result_mock.to_pandas.return_value = df
    return result_mock


def test_gate_passes_when_all_metrics_above_floor():
    """§13.9: gate returns True when all metrics satisfy min and max_regression."""
    mod, client_mock = _load_gate_module()

    candidate_scores = {
        "booking_quality": 0.90,
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }
    baseline_scores = {
        "booking_quality": 0.91,
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }

    client_mock.evaluate.return_value = _make_pandas_mock(candidate_scores)
    baseline_mock = MagicMock()
    baseline_mock.feedback_stats = {
        k: {"avg": v} for k, v in baseline_scores.items()
    }
    client_mock.read_experiment.return_value = baseline_mock

    mod.langsmith_client = client_mock
    result = mod.run_promotion_gate("staging-golden-set", "exp-baseline-001", pr_number=42)

    assert result is True


def test_gate_blocks_when_metric_below_absolute_floor():
    """§13.9: gate returns False when booking_quality drops below 0.87 floor."""
    mod, client_mock = _load_gate_module()

    candidate_scores = {
        "booking_quality": 0.80,   # below floor of 0.87
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }
    baseline_scores = {
        "booking_quality": 0.91,
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }

    client_mock.evaluate.return_value = _make_pandas_mock(candidate_scores)
    baseline_mock = MagicMock()
    baseline_mock.feedback_stats = {
        k: {"avg": v} for k, v in baseline_scores.items()
    }
    client_mock.read_experiment.return_value = baseline_mock

    mod.langsmith_client = client_mock
    result = mod.run_promotion_gate("staging-golden-set", "exp-baseline-001", pr_number=42)

    assert result is False


def test_gate_blocks_when_regression_exceeds_limit():
    """§13.9: gate returns False when regression exceeds max_regression (0.03) even above floor."""
    mod, client_mock = _load_gate_module()

    candidate_scores = {
        "booking_quality": 0.88,   # above floor but regressed 0.05 from baseline 0.93
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }
    baseline_scores = {
        "booking_quality": 0.93,   # delta = 0.05 > max_regression 0.03
        "no_hallucination": 0.95,
        "tool_call_correct": 0.92,
    }

    client_mock.evaluate.return_value = _make_pandas_mock(candidate_scores)
    baseline_mock = MagicMock()
    baseline_mock.feedback_stats = {
        k: {"avg": v} for k, v in baseline_scores.items()
    }
    client_mock.read_experiment.return_value = baseline_mock

    mod.langsmith_client = client_mock
    result = mod.run_promotion_gate("staging-golden-set", "exp-baseline-001", pr_number=42)

    assert result is False

def test_main_missing_args_exits_2():
    """Missing CLI args print usage and exit 2, without a traceback."""
    mod, _ = _load_gate_module()
    with pytest.raises(SystemExit) as caught:
        mod.main([])
    assert caught.value.code == 2


def test_offline_gate_passes_without_langsmith_key(monkeypatch):
    mod, _ = _load_gate_module()
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    mod.langsmith_client = None
    assert mod.run_promotion_gate("staging-golden-set", "exp-baseline", 7) is True

