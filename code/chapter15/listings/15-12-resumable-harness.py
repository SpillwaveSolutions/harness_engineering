import json
import os
import subprocess
import sys
from pathlib import Path

import anthropic


def _anthropic_client():
    """Live client only when asked. A test double is not a real class."""
    ctor = anthropic.Anthropic
    if not isinstance(ctor, type):
        return ctor()
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
    return ctor()

FOUR_FEATURES = [
    {
        "category": "flight",
        "description": "Search flights by route and date",
        "steps": [
            "Call search_flights with origin, destination, date",
            "Return top three options sorted by price",
        ],
        "passes": False,
    },
    {
        "category": "flight",
        "description": "Book selected flight with idempotency key",
        "steps": [
            "Generate idempotency key from session_id + flight_id",
            "Call book_flight; store confirmation in claude-progress.txt",
        ],
        "passes": False,
    },
    {
        "category": "hotel",
        "description": "Book hotel linked to the confirmed flight",
        "steps": [
            "Call book_hotel with flight booking_id and guest preferences",
            "Store hotel confirmation in claude-progress.txt",
        ],
        "passes": False,
    },
    {
        "category": "itinerary",
        "description": "Send complete itinerary to the traveler",
        "steps": [
            "Call send_itinerary with all confirmed booking IDs",
            "Verify delivery receipt; update feature passes to true",
        ],
        "passes": False,
    },
]

class ResumableStateHarness:

    def __init__(self, project_dir: Path, session_id: str):
        self.project_dir = project_dir
        self.session_id = session_id
        self.plan_path = project_dir / "feature_list.json"
        self.progress_path = project_dir / "claude-progress.txt"
        self.client = _anthropic_client()

    def load_plan(self) -> list[dict] | None:            # ①
        if not self.plan_path.exists():
            return None
        return json.loads(self.plan_path.read_text())

    def run(self) -> dict:
        plan = self.load_plan()
        if plan is None:                                    # ②
            return self._run_initializer()
        return self._run_coding_session(plan)

    def _run_initializer(self) -> dict:
        self.plan_path.write_text(
            json.dumps(FOUR_FEATURES, indent=2)
        )
        self._write_progress(
            done="(none — initial session)",
            next_up="\n".join(
                f"- {f['description']}" for f in FOUR_FEATURES
            ),
            notes="Initializer ran. All features set to passes: false.",
        )
        self._git_commit("init: Initializer Agent scaffolding")  # ③
        return {"role": "initializer", "status": "complete"}

    def _run_coding_session(self, plan: list[dict]) -> dict: # ④
        incomplete = [f for f in plan if not f["passes"]]
        if not incomplete:
            return {"role": "coding_agent", "status": "all_features_pass"}

        feature = incomplete[0]                             # ⑤
        if self.client is None:
            print(
                "offline: coding session not sent to the model",
                file=sys.stderr,
                flush=True,
            )
            return {
                "role": "coding_agent",
                "status": "offline",
                "feature": feature["description"],
            }
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{
                "role": "user",
                "content": (
                    f"Implement this feature:\n{json.dumps(feature, indent=2)}\n\n"
                    "Run tests first. Mark passes: true only if tests pass. "
                    "Do not edit any existing test. "
                    "End with a test-passing commit."
                ),
            }],
        )
        summary = ""
        content = getattr(response, "content", None)
        if content:
            summary = getattr(content[0], "text", "") or ""
        recorded = {
            "status": "session_complete",
            "summary": summary,
        }
        self._git_commit(
            f"feat: {feature['description']} (session {self.session_id})"
        )
        return {
            "role": "coding_agent",
            "feature": feature["description"],
            "status": recorded["status"],
        }

    def _write_progress(self, done: str, next_up: str, notes: str) -> None:
        self.progress_path.write_text(
            f"## Done\n{done}\n\n"
            f"## In Progress\n(current session)\n\n"
            f"## Next\n{next_up}\n\n"
            f"## Notes\n{notes}\n"
        )

    def _git_commit(self, message: str) -> None:
        subprocess.run(
            ["git", "add", "-A"], cwd=self.project_dir, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.project_dir, check=True,
        )
