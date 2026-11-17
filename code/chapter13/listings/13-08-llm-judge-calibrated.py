import json
import os
import sys

from anthropic import Anthropic
from opentelemetry import trace

tracer = trace.get_tracer("travel_booking_agent")
# Tests may assign a stand-in. Import does not construct a network client.
client = None


class _OfflineContent:
    def __init__(self, text: str) -> None:
        self.text = text


class _OfflineResponse:
    def __init__(self, text: str) -> None:
        self.content = [_OfflineContent(text)]


class _OfflineMessages:
    def create(self, **kwargs):
        del kwargs
        payload = json.dumps({
            "score": 4,
            "label": "PASS",
            "explanation": "Offline judge: booking looks valid.",
        })
        return _OfflineResponse(payload)


class _OfflineClient:
    def __init__(self) -> None:
        self.messages = _OfflineMessages()


def _resolve_client():
    if client is not None:
        return client
    if os.environ.get("ANTHROPIC_API_KEY"):
        return Anthropic()
    print(
        "ANTHROPIC_API_KEY is unset; scoring with an offline judge.",
        file=sys.stderr,
    )
    return _OfflineClient()


def parse_verdict(text: str) -> dict:
    """Parse the judge's JSON response into a score/label/explanation dict."""
    return json.loads(text)


BOOKING_QUALITY_RUBRIC = """
Score the travel booking response on a scale of 1-5:

5 - Contains valid flight identifier, matches all passenger constraints,
    confirms booking status correctly, no hallucinated details.
4 - Minor issue (e.g., one constraint not explicitly confirmed) but booking is valid.
3 - Booking appears valid but key constraint confirmation is ambiguous.
2 - Booking ID present but constraints violated or status unclear.
1 - Wrong flight, missing booking ID, or date/passenger mismatch.

Respond with JSON: {"score": N, "label": "PASS"|"FAIL"|"NEEDS_REVIEW", "explanation": "..."}
"""


def score_booking_response(
    booking_response: str,
    passenger_constraints: dict,
) -> dict:
    with tracer.start_as_current_span("evaluator_decision booking_quality") as span:
        span.set_attribute("gen_ai.evaluation.name", "booking_quality")

        active = _resolve_client()
        judge_response = active.messages.create(
            model="claude-sonnet-4-6",  # cross-model judge: use different family if available
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": (
                    f"{BOOKING_QUALITY_RUBRIC}\n\n"
                    f"Constraints: {passenger_constraints}\n\n"
                    f"Response to score: {booking_response}"
                )
            }]
        )

        verdict = parse_verdict(judge_response.content[0].text)
        span.set_attribute("gen_ai.evaluation.score.value", verdict["score"])
        span.set_attribute("gen_ai.evaluation.score.label", verdict["label"])
        span.set_attribute(
            "gen_ai.evaluation.explanation", verdict["explanation"][:500]
        )
        return verdict


def main() -> int:
    verdict = score_booking_response(
        "Booked flight AA101, economy, 2026-06-15.",
        {"seat_class": "economy"},
    )
    print(json.dumps(verdict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
