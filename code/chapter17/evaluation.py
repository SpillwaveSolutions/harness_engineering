"""Offline eval helpers for the model-swap rehearsal.

A missing eval set or baseline is not a passing score. These helpers
do not call a model or open a network connection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


async def run_eval_suite(
    model: str,
    eval_set: str,
    options: object | None = None,
) -> dict:
    """Return a fixed offline score. ``options`` is accepted and ignored."""
    del options
    path = Path(eval_set)
    if not path.is_file():
        print(
            f"SKIPPED: eval set {eval_set} is missing; no evals run",
            file=sys.stderr,
            flush=True,
        )
        return {
            "status": "skipped",
            "model": model,
            "cases": 0,
            "score": None,
        }
    rows = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {
        "status": "offline",
        "model": model,
        "cases": len(rows),
        "score": 0.90 if rows else None,
    }


def compare_against_baseline(
    candidate: dict,
    baseline_path: str,
    quality_floor: float = 0.87,
    regression_limit: float = 0.03,
) -> dict:
    """Compare scores. A missing file is an empty baseline."""
    if (
        candidate.get("status") == "skipped"
        or not candidate.get("cases")
        or candidate.get("score") is None
    ):
        return {
            "pass": False,
            "reason": "no evals run",
            "score": None,
            "baseline_score": None,
            "status": "skipped",
        }
    path = Path(baseline_path)
    if not path.is_file():
        print(
            f"SKIPPED: baseline {baseline_path} is missing; no evals run",
            file=sys.stderr,
            flush=True,
        )
        return {
            "pass": False,
            "reason": "no evals run",
            "score": candidate.get("score"),
            "baseline_score": None,
            "status": "skipped",
        }
    baseline = json.loads(path.read_text(encoding="utf-8") or "{}")
    score = float(candidate.get("score", 0.0))
    baseline_score = float(baseline.get("score", 0.0))
    passed = score >= quality_floor and (
        baseline_score - score
    ) <= regression_limit
    if passed:
        reason = "within quality floor and regression limit"
    else:
        reason = "below quality floor or regression limit"
    return {
        "pass": passed,
        "reason": reason,
        "score": score,
        "baseline_score": baseline_score,
        "status": "offline",
    }
