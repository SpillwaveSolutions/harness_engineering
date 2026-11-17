from dataclasses import dataclass

# Absolute floor and max regression per quality metric.    ①
# Values match §14.11 dual-threshold defaults.
thresholds: dict[str, dict[str, float]] = {
    "booking_quality": {
        "min": 0.87,
        "max_regression": 0.03,
    },
}

# Budget ceiling per cost metric (USD).                    ②
cost_thresholds: dict[str, float] = {
    "cost_usd_per_session": 0.50,
}


@dataclass
class GateResult:
    passed: bool
    lane_results: dict[str, dict]  # lane_name -> {passed, score, detail}


def run_promotion_gate(
    quality_scores: dict[str, float],
    safety_results: dict[str, bool],
    cost_metrics: dict[str, float],
    policy_checks: dict[str, bool],
    baseline_scores: dict[str, float],
) -> GateResult:
    """
    Four-lane AND gate. All four lanes must pass.
    Returns structured result for CI reporting.
    """
    lane_results = {}

    # Quality lane: absolute floor + regression limit                ①
    quality_pass = all(
        quality_scores.get(metric, 0) >= thresholds[metric]["min"]
        and (baseline_scores.get(metric, 1.0) - quality_scores.get(metric, 0))
            <= thresholds[metric]["max_regression"]
        for metric in thresholds
    )
    lane_results["quality"] = {"passed": quality_pass, "scores": quality_scores}

    # Safety lane: all safety tests must pass                        ②
    safety_pass = all(safety_results.values())
    lane_results["safety"] = {"passed": safety_pass, "results": safety_results}

    # Cost lane: all metrics within budget ceiling                   ③
    cost_pass = all(
        cost_metrics.get(k, 0) <= cost_thresholds[k]
        for k in cost_thresholds
    )
    lane_results["cost"] = {"passed": cost_pass, "metrics": cost_metrics}

    # Policy lane: all policy checks must pass                       ④
    policy_pass = all(policy_checks.values())
    lane_results["policy"] = {"passed": policy_pass, "checks": policy_checks}

    all_passed = quality_pass and safety_pass and cost_pass and policy_pass
    return GateResult(passed=all_passed, lane_results=lane_results)
