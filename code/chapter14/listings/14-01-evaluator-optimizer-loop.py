from __future__ import annotations

import json
import logging
import os
import sys

from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Injected by tests. A live client is built only when a run asks for one.
client = None


def _client():
    """Return an injected or live client, or None when staying offline."""
    global client
    if client is not None:
        return client
    if os.environ.get("HARNESS_LIVE_API") != "1":
        print(
            "offline: HARNESS_LIVE_API is not 1",
            file=sys.stderr,
            flush=True,
        )
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is unset; returning offline result",
            file=sys.stderr,
            flush=True,
        )
        return None
    client = Anthropic()
    return client

# The full rubric lives in listing 14-02. This prompt is the offline stand-in.
JUDGE_SYSTEM_PROMPT = """
You are an independent evaluator for a travel-booking agent.
Score each field 1-5. Output valid JSON only.
"""


def generate_booking_response(
    booking_prompt: str,
    feedback: str | None = None,
) -> str:
    """
    Call the generator model, or return a fixed offline booking.
    The full tool-use loop from Chapter 2 is not in this file.
    """
    messages: list[dict] = [{"role": "user", "content": booking_prompt}]
    if feedback:
        messages.append(
            {"role": "user", "content": f"Previous attempt feedback:\n{feedback}"}
        )
    del messages
    preview = booking_prompt[:40]
    return (
        f"Booking response for: {preview}. "
        "flight_id=AA100 passenger=offline price_usd=420"
    )


def assemble_feedback(verdict: dict) -> str:
    """
    Build a feedback string from the evaluator verdict.
    The generator receives this; the rubric stays out-of-band.
    """
    explanation = verdict.get("explanation", "")
    label = verdict.get("label", "UNKNOWN")
    return f"Previous output scored {label}. Details: {explanation}"


def run_evaluator_optimizer(
    booking_prompt: str,
    max_iterations: int = 3,
    max_budget_usd: float = 0.50,
) -> dict:
    """
    Evaluator-optimizer loop for the travel-booking harness.
    The evaluator runs out-of-band; the generator never sees the rubric.
    """
    candidate = generate_booking_response(booking_prompt)           # ①
    iteration = 0
    total_cost = 0.0

    while iteration < max_iterations:
        verdict = evaluate_booking_response(candidate)              # ②
        total_cost += verdict["cost_usd"]

        if total_cost > max_budget_usd:
            return {
                "status": "budget_exceeded",
                "last_candidate": candidate,
            }

        if verdict["label"] == "PASS":                              # ③
            return {
                "status": "pass",
                "output": candidate,
                "iterations": iteration,
            }

        feedback = assemble_feedback(verdict)                       # ④
        candidate = generate_booking_response(
            booking_prompt, feedback=feedback
        )
        iteration += 1

    return {
        "status": "max_iterations",
        "last_candidate": candidate,
        "verdict": verdict,
    }


def evaluate_booking_response(candidate: str) -> dict:
    """Harness-controlled evaluation call. Runs as a separate API call."""
    api = _client()
    if api is None:
        return {
            "status": "offline",
            "label": "NEEDS_REVIEW",
            "explanation": "offline result; model was not called",
            "cost_usd": 0.0,
        }
    response = api.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Evaluate this booking response:\n\n{candidate}",
            }
        ],
    )
    result = json.loads(response.content[0].text)
    # Ensure cost_usd is present for budget tracking.
    if "cost_usd" not in result:
        result["cost_usd"] = 0.0
    return result
