# gates/run_promotion_gate.py
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
from typing import ClassVar

# Import run_promotion_gate from listing 14-07 when that file is present.
_listing_07_path = (
    pathlib.Path(__file__).parent / "14-07-promotion-gate.py"
)
if _listing_07_path.exists():
    _spec = importlib.util.spec_from_file_location(
        "listing_14_07", _listing_07_path
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)          # type: ignore[union-attr]
    run_promotion_gate = _mod.run_promotion_gate
    GateResult = _mod.GateResult
else:
    def run_promotion_gate(**kwargs):        # type: ignore[misc]
        """Offline fallback when 14-07 is not beside this file."""
        del kwargs
        raise RuntimeError("14-07 listing not present")

    class GateResult:                       # type: ignore[no-redef]
        passed = False
        lane_results: ClassVar[dict] = {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the promotion gate script."""
    parser = argparse.ArgumentParser(
        description="Run the four-lane promotion gate."
    )
    parser.add_argument(
        "--baseline-scores",
        required=True,
        help="Path to baseline scores JSON file.",
    )
    parser.add_argument(
        "--eval-dataset",
        required=True,
        help="Path to evaluation dataset JSON file.",
    )
    return parser.parse_args(argv)


def load_json(path: str) -> dict:
    """Load a JSON file from *path* and return the parsed dict."""
    return json.loads(pathlib.Path(path).read_text())


def run_eval_sweep(eval_dataset_path: str) -> dict:
    """
    Load eval dataset and return lane results keyed by lane name.
    In production this invokes §14.10 batch evaluation; here we
    return the dataset payload as-is so structural tests pass.
    """
    data = load_json(eval_dataset_path)
    return {
        "quality": data.get("quality", {}),
        "safety": data.get("safety", {}),
        "cost": data.get("cost", {}),
        "policy": data.get("policy", {}),
    }


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    baseline = load_json(args.baseline_scores)
    eval_results = run_eval_sweep(args.eval_dataset)

    gate_result = run_promotion_gate(
        quality_scores=eval_results["quality"],
        safety_results=eval_results["safety"],
        cost_metrics=eval_results["cost"],
        policy_checks=eval_results["policy"],
        baseline_scores=baseline,
    )

    print(json.dumps(gate_result.lane_results, indent=2))

    sys.exit(0 if gate_result.passed else 1)           # ①


if __name__ == "__main__":
    main()
