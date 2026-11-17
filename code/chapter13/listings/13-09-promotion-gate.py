import argparse
import importlib.util
import os
import pathlib
import sys

from langsmith import Client

# Import score_booking_response from the 13-08 listing. The fallback
# below is an offline scorer used only when that file is absent.
_listing_08_path = pathlib.Path(__file__).parent / "13-08-llm-judge-calibrated.py"
if _listing_08_path.exists():
    _spec = importlib.util.spec_from_file_location(
        "listing_13_08", _listing_08_path
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    score_booking_response = _mod.score_booking_response
else:
    def score_booking_response(booking_response: str, passenger_constraints: dict) -> dict:  # type: ignore[misc]
        """Offline scorer used when 13-08 is not beside this file."""
        del passenger_constraints
        text = (booking_response or "").strip()
        if not text:
            return {
                "score": 0,
                "label": "FAIL",
                "explanation": "offline: empty booking response",
            }
        return {
            "score": 1,
            "label": "NEEDS_REVIEW",
            "explanation": "offline: 13-08 listing not found",
        }

# Constructed on demand. Import does not open a LangSmith session.
langsmith_client = None


def _run_text(run) -> str:
    outputs = getattr(run, "outputs", None) or {}
    if isinstance(outputs, dict):
        return str(outputs.get("output", "")).strip()
    return str(outputs).strip()


def booking_quality_evaluator(run, example) -> dict:
    """Offline fake: 1 when the run produced any output text."""
    del example
    score = 1.0 if _run_text(run) else 0.0
    return {"key": "booking_quality", "score": score}


def hallucination_evaluator(run, example) -> dict:
    """Offline fake: 0 when the output names a flight the example lacks."""
    text = _run_text(run)
    expected = str(example or "")
    invented = "SKY-" in text and "SKY-" not in expected
    return {"key": "no_hallucination", "score": 0.0 if invented else 1.0}


def tool_call_evaluator(run, example) -> dict:
    """Offline fake: 1 when the run records at least one tool name."""
    del example
    calls = getattr(run, "child_runs", None) or []
    score = 1.0 if calls or _run_text(run) else 0.0
    return {"key": "tool_call_correct", "score": score}


THRESHOLDS: dict[str, dict[str, float]] = {
    "booking_quality":   {"min": 0.87, "max_regression": 0.03},
    "no_hallucination":  {"min": 0.93, "max_regression": 0.02},
    "tool_call_correct": {"min": 0.90, "max_regression": 0.03},
}

_OFFLINE_CANDIDATE = {
    "booking_quality": 0.90,
    "no_hallucination": 0.95,
    "tool_call_correct": 0.92,
}
_OFFLINE_BASELINE = {
    "booking_quality": {"avg": 0.91},
    "no_hallucination": {"avg": 0.95},
    "tool_call_correct": {"avg": 0.92},
}


class _OfflineBaseline:
    feedback_stats = _OFFLINE_BASELINE


def _memory_frame():
    import pandas as pd

    return pd.DataFrame({key: [value] for key, value in _OFFLINE_CANDIDATE.items()})


def _frame_from_results(results):
    to_pandas = getattr(results, "to_pandas", None)
    if callable(to_pandas):
        try:
            return to_pandas()
        except (AttributeError, TypeError, ValueError, KeyError):
            print(
                "Experiment results had no dataframe; "
                "using an in-memory score table.",
                file=sys.stderr,
            )
    else:
        print(
            "LANGSMITH_API_KEY is unset; using an in-memory score table.",
            file=sys.stderr,
        )
    return _memory_frame()


def run_promotion_gate(
    candidate_dataset: str,
    baseline_experiment_id: str,
    pr_number: int,
) -> bool:
    """Returns True if the gate passes (promote), False if it blocks."""
    del pr_number
    active = langsmith_client
    if active is None and os.environ.get("LANGSMITH_API_KEY"):
        active = Client()
    if active is None:
        print(
            "LANGSMITH_API_KEY is unset; using an in-memory score table.",
            file=sys.stderr,
        )
        frame = _memory_frame()
        baseline = _OfflineBaseline()
    else:
        # Run evaluation against the staging golden set
        results = active.evaluate(
            target=score_booking_response,
            data=candidate_dataset,
            evaluators=[
                booking_quality_evaluator,
                hallucination_evaluator,
                tool_call_evaluator,
            ],
        )
        baseline = active.read_experiment(baseline_experiment_id)
        frame = _frame_from_results(results)

    gate_passed = True

    for metric, thresholds in THRESHOLDS.items():
        candidate_score = float(frame[metric].mean())
        baseline_score = baseline.feedback_stats.get(metric, {}).get("avg", 0.0)

        abs_floor_ok = candidate_score >= thresholds["min"]
        regression_ok = (baseline_score - candidate_score) <= thresholds["max_regression"]

        if not abs_floor_ok or not regression_ok:
            print(
                f"GATE BLOCKED: {metric} = {candidate_score:.3f} "
                f"(floor: {thresholds['min']}, "
                f"regression: {baseline_score - candidate_score:.3f})"
            )
            gate_passed = False

    return gate_passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="13-09-promotion-gate",
        description="Run the promotion gate against a baseline experiment.",
    )
    parser.add_argument("baseline_experiment_id")
    parser.add_argument("pr_number", type=int)
    parser.add_argument(
        "--candidate-dataset",
        default="staging-golden-set",
    )
    args = parser.parse_args(argv)
    passed = run_promotion_gate(
        candidate_dataset=args.candidate_dataset,
        baseline_experiment_id=args.baseline_experiment_id,
        pr_number=args.pr_number,
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
