"""Listing 14-10: Wiring the evaluator-optimizer into the harness via hooks.

The `agents` import is the offline hook stand-in in
`code/chapter14/listings/agents.py`. It allows or blocks tool calls
in-process and does not call the agent SDK.
"""
from __future__ import annotations

import importlib.util
import logging
import pathlib
import sys

# Running this file puts listings/ on sys.path. Loading it from the chapter
# root does not, so the sibling agents module would be missing.
_LISTINGS = pathlib.Path(__file__).resolve().parent
if str(_LISTINGS) not in sys.path:
    sys.path.insert(0, str(_LISTINGS))

# agents.py is the offline hook stand-in (AgentHooks + HookResult).
from agents import AgentHooks, HookResult  # type: ignore[import]

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Load sibling listings when they are present.
# --------------------------------------------------------------------------
_listings_dir = pathlib.Path(__file__).parent


def _load_listing(filename: str, module_name: str):
    path = _listings_dir / filename
    if path.exists():
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)    # type: ignore[union-attr]
        return mod
    return None


_mod_01 = _load_listing(
    "14-01-evaluator-optimizer-loop.py", "listing_14_01"
)
_mod_04 = _load_listing("14-04-calibration-fit.py", "listing_14_04")

if _mod_01 is not None:
    run_evaluator_optimizer = _mod_01.run_evaluator_optimizer
else:
    def run_evaluator_optimizer(booking_prompt: str, **kwargs) -> dict:
        """Offline result when listing 14-01 is not beside this file."""
        return {
            "status": "offline",
            "booking_prompt": booking_prompt,
            "label": "NEEDS_REVIEW",
        }

if _mod_04 is not None:
    apply_calibration = _mod_04.apply_calibration
else:
    def apply_calibration(                  # type: ignore[misc]
        raw_scores: dict, calibrators: dict
    ) -> dict:
        """Return the raw scores when listing 14-04 is not beside this file."""
        return raw_scores


# Placeholder calibrators; in production these are trained objects
# produced by listing 14-04 and persisted in the harness artefact store.
CALIBRATORS: dict = {}


def format_booking_for_eval(
    tool_name: str,
    tool_input: dict,
) -> str:
    """Serialise a proposed tool call into an evaluable candidate string."""
    return f"Tool: {tool_name}\nInput: {tool_input}"


class EvaluationHooks(AgentHooks):
    """
    Wires the evaluator-optimizer loop into the harness via PreToolUse.
    High-stakes booking actions are evaluated before commitment.
    """

    EVALUATED_TOOLS: frozenset[str] = frozenset({"book_flight"})

    def pre_tool_use(
        self,
        tool_name: str,
        tool_input: dict,
    ) -> HookResult:
        if tool_name not in self.EVALUATED_TOOLS:
            return HookResult.allow()                                   # ①

        # Format the proposed booking as an evaluable candidate.
        candidate = format_booking_for_eval(tool_name, tool_input)

        # Run the evaluator-optimizer loop out-of-band.                ②
        eval_result = run_evaluator_optimizer(
            booking_prompt=candidate,
            max_iterations=3,
        )

        if eval_result["status"] == "pass":
            score = eval_result.get("final_score", {})
            calibrated = apply_calibration(score, CALIBRATORS)         # ③
            # 0.85: 5 points below the §14.7 auto-proceed tier (0.90)
            # to allow one retry before the gate blocks.
            if all(v >= 0.85 for v in calibrated.values()):
                return HookResult.allow()
            else:
                return HookResult.block(
                    reason=(
                        "Calibrated confidence below threshold: "
                        f"{calibrated}"
                    )
                )
        else:
            return HookResult.block(
                reason=f"Evaluator returned {eval_result['status']}"
            )
