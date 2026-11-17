"""Tests for listing 14-04-calibration-fit (§14.7).

Verifies:
  - Module defines fit_calibration_model and apply_calibration.
  - fit_calibration_model returns a fitted calibration object.
  - apply_calibration returns calibrated probabilities in [0, 1].
  - Uncalibrated fields pass through unchanged.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "14-04-calibration-fit.py"
    spec = importlib.util.spec_from_file_location(
        "listing_14_04", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_04"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_defines_both_functions():
    """§14.7: listing must define fit_calibration_model and apply_calibration."""
    mod = _load_module()
    assert callable(getattr(mod, "fit_calibration_model", None))
    assert callable(getattr(mod, "apply_calibration", None))


def test_fit_calibration_model_returns_fitted_object():
    """§14.7: fit_calibration_model must return a fitted calibrator."""
    mod = _load_module()
    # 20 samples split evenly: enough for 5-fold CV.
    scores = [1.0, 1.5, 2.0, 2.5, 1.2] * 2 + [3.5, 4.0, 4.5, 5.0, 3.8] * 2
    labels = [0] * 10 + [1] * 10
    calibrator = mod.fit_calibration_model(
        scores, labels, method="sigmoid"
    )
    # The returned object must have predict_proba (sklearn interface).
    assert hasattr(calibrator, "predict_proba"), (
        "fit_calibration_model must return an object with predict_proba"
    )


def test_apply_calibration_returns_dict_in_unit_interval():
    """§14.7: calibrated scores must be in [0, 1]."""
    mod = _load_module()
    scores = [1.0, 1.5, 2.0, 2.5, 1.2] * 2 + [3.5, 4.0, 4.5, 5.0, 3.8] * 2
    labels = [0] * 10 + [1] * 10
    calibrator = mod.fit_calibration_model(
        scores, labels, method="sigmoid"
    )

    raw = {"booking_quality": 4.0}
    calibrators = {"booking_quality": calibrator}
    result = mod.apply_calibration(raw, calibrators)

    assert "booking_quality" in result
    assert 0.0 <= result["booking_quality"] <= 1.0


def test_apply_calibration_passthrough_for_uncalibrated_field():
    """§14.7: fields without a calibrator pass through unchanged."""
    mod = _load_module()
    raw = {"unknown_field": 0.77}
    result = mod.apply_calibration(raw, calibrators={})
    assert result["unknown_field"] == pytest.approx(0.77)
