from __future__ import annotations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression


def fit_calibration_model(
    judge_scores: list[float],
    human_labels: list[int],  # 1=correct, 0=incorrect
    method: str = "sigmoid",  # "sigmoid" (Platt) for <1000; "isotonic" for >=1000
) -> CalibratedClassifierCV:
    """
    Fit a calibration model on a labelled validation set.
    Returns a calibrated classifier that transforms raw judge scores
    into calibrated probabilities.
    """
    X = np.array(judge_scores).reshape(-1, 1)
    y = np.array(human_labels)

    # Platt Scaling (sigmoid) works with <1000 samples              ①
    # Isotonic regression overfits below 1000; use only with >=1000 ②
    # cv=5 uses cross-validation to fit and calibrate jointly.
    base = LogisticRegression()
    calibrated = CalibratedClassifierCV(
        base, method=method, cv=5
    )
    calibrated.fit(X, y)
    return calibrated


def apply_calibration(
    raw_scores: dict[str, float],
    calibrators: dict[str, CalibratedClassifierCV],
) -> dict[str, float]:
    """Apply field-level calibration to raw judge scores."""
    calibrated: dict[str, float] = {}
    for field, score in raw_scores.items():
        if field in calibrators:
            X = np.array([[score]])
            calibrated[field] = float(
                calibrators[field].predict_proba(X)[0][1]
            )
        else:
            # Uncalibrated; pass through and flag for review.
            calibrated[field] = score
    return calibrated
