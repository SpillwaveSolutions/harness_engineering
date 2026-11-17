# Quarterly model-swap rehearsal script for the travel-booking harness
# Run this against staging before the provider forces it in production

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from claude_agent_sdk import ClaudeAgentOptions
from evaluation import compare_against_baseline, run_eval_suite

PRODUCTION_MODEL = "claude-sonnet-4-6"
CANDIDATE_MODEL = "claude-sonnet-4-7"  # hypothetical next version   # ①


async def rehearse_model_swap() -> dict:
    # Step 1: run eval suite against candidate model in staging
    candidate_scores = await run_eval_suite(
        model=CANDIDATE_MODEL,
        eval_set="evals/travel_booking_v3.jsonl",   # §14.6 eval set
        options=ClaudeAgentOptions(
            allowed_tools=[
                "mcp__travel__search_flights",
                "mcp__travel__book_flight",
            ],
        ),
    )

    # Step 2: compare against production baseline                     # ②
    verdict = compare_against_baseline(
        candidate=candidate_scores,
        baseline_path="evals/baselines/production.json",
        quality_floor=0.87,        # §14.11 dual-threshold gate
        regression_limit=0.03,
    )

    # Step 3: document and decide                                     # ③
    if verdict.get("status") == "skipped" or not verdict["pass"]:
        if verdict.get("reason") == "no evals run":
            print(f"SKIPPED: no evals run for {CANDIDATE_MODEL}")
        else:
            print(f"FAIL: {verdict['reason']} — rollback or investigate")
    else:
        print(f"PASS: {CANDIDATE_MODEL} ready for promotion")

    return verdict


def main() -> int:
    verdict = asyncio.run(rehearse_model_swap())
    if verdict.get("status") == "skipped" or not verdict.get("pass"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
