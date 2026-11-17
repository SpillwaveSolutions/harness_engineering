"""Tests for listing 14-05-stratified-sampler (§14.8).

Verifies:
  - Module defines stratified_sample and SampledOutput dataclass.
  - stratified_sample distributes outputs into three strata correctly.
  - Samples per stratum are capped at samples_per_stratum.
  - Empty strata produce no samples (no crash).
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "14-05-stratified-sampler.py"
    spec = importlib.util.spec_from_file_location(
        "listing_14_05", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_05"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def _make_outputs(mod, scores: list[float]) -> list:
    return [
        mod.SampledOutput(
            output_id=f"out-{i}",
            calibrated_score=s,
            stratum="",
            booking_metadata={},
        )
        for i, s in enumerate(scores)
    ]


def test_module_defines_stratified_sample_and_dataclass():
    """§14.8: listing must define stratified_sample and SampledOutput."""
    mod = _load_module()
    assert callable(getattr(mod, "stratified_sample", None))
    assert hasattr(mod, "SampledOutput")


def test_high_confidence_stratum():
    """§14.8: scores >= 0.90 land in high_confidence stratum."""
    mod = _load_module()
    outputs = _make_outputs(mod, [0.91, 0.95, 0.99])
    result = mod.stratified_sample(outputs, samples_per_stratum=10)
    assert len(result) == 3


def test_medium_confidence_stratum():
    """§14.8: 0.70 <= score < 0.90 land in medium_confidence stratum."""
    mod = _load_module()
    outputs = _make_outputs(mod, [0.75, 0.80, 0.89])
    result = mod.stratified_sample(outputs, samples_per_stratum=10)
    assert len(result) == 3


def test_low_confidence_stratum():
    """§14.8: scores < 0.70 land in low_confidence stratum."""
    mod = _load_module()
    outputs = _make_outputs(mod, [0.50, 0.60, 0.65])
    result = mod.stratified_sample(outputs, samples_per_stratum=10)
    assert len(result) == 3


def test_samples_capped_at_samples_per_stratum():
    """§14.8: no stratum returns more than samples_per_stratum samples."""
    mod = _load_module()
    # 5 high-confidence outputs, limit = 3
    outputs = _make_outputs(mod, [0.91, 0.92, 0.93, 0.94, 0.95])
    result = mod.stratified_sample(outputs, samples_per_stratum=3)
    assert len(result) <= 3


def test_empty_input_returns_empty():
    """§14.8: empty input produces empty output without crash."""
    mod = _load_module()
    result = mod.stratified_sample([], samples_per_stratum=10)
    assert result == []
