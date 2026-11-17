from __future__ import annotations

import json
import logging
import os
import sys

import anthropic

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
    client = anthropic.Anthropic()
    return client

# Stub: full rubric defined in listing 14-02; imported here for
# module independence so structural tests do not need 14-02.
JUDGE_SYSTEM_PROMPT = """
You are an independent evaluator for a travel-booking agent.
Score each field 1-5. Output valid JSON only.
"""


def parse_verdict(message: object) -> dict:
    """
    Extract the structured verdict dict from a completed batch message.
    Mirrors listing 14-02's parse_verdict; defined here so this module
    is self-contained for structural import tests.
    """
    if hasattr(message, "content") and message.content:
        text = message.content[0].text
        return json.loads(text)
    return {"label": "PARSE_ERROR"}


def build_eval_requests(
    trace_samples: list[dict],  # list of {trace_id, booking_output}
) -> list[dict]:
    """Batch request dicts. No client and no API key required."""
    requests: list[dict] = []
    for sample in trace_samples:
        requests.append({
            "custom_id": sample["trace_id"],  # correlation key ①
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 512,
                "system": JUDGE_SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Evaluate booking output:\n\n"
                            f"{sample['booking_output']}"
                        ),
                    }
                ],
            },
        })
    return requests


def submit_eval_batch(
    trace_samples: list[dict],  # list of {trace_id, booking_output}
) -> str:
    """
    Submit a batch evaluation job. Returns batch_id for polling.
    custom_id is the correlation key — results arrive out of order.
    """
    requests = build_eval_requests(trace_samples)
    api = _client()
    if api is None:
        return "offline"
    batch = api.messages.batches.create(requests=requests)
    return batch.id


def collect_batch_results(batch_id: str) -> dict[str, dict]:
    """
    Iterate results. Results arrive out of order; custom_id is the join key.
    Handle partial failures without aborting the sweep.
    """
    api = _client()
    if api is None:
        return {"offline": {"label": "OFFLINE", "batch_id": batch_id}}
    results: dict[str, dict] = {}
    for result in api.messages.batches.results(batch_id):
        custom_id = result.custom_id                                # ②
        if result.result.type == "succeeded":
            results[custom_id] = parse_verdict(
                result.result.message
            )
        elif result.result.type == "errored":
            results[custom_id] = {
                "label": "EVAL_ERROR",                              # ③
                "error": result.result.error.type,
            }
        elif result.result.type == "expired":
            results[custom_id] = {"label": "EVAL_EXPIRED"}
    return results
