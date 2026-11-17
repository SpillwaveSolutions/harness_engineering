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


_OFFLINE_FEATURES = [
    {
        "category": "flight",
        "description": "Search flights by route and date",
        "steps": ["Call search_flights"],
        "passes": False,
    },
]

INIT_PROMPT = """
You are the Initializer Agent for the travel-booking harness.
Your job is to decompose the project into a feature_list.json,
create acceptance tests for each feature, write claude-progress.txt
with the project context, and make the initial Git commit.

Be ambitious about scope. Stay focused on high-level design.
Do NOT implement any feature. Set the table for the Coding Agent.

Features to decompose:
1. Search flights (search_flights tool, validated parameters)
2. Book flight (book_flight tool, idempotency-keyed, confirmation stored)
3. Book hotel (book_hotel tool, linked to flight booking_id)
4. Send itinerary (send_itinerary tool, full trip details)

Output feature_list.json with the schema:
[{"category": str, "description": str, "steps": [str], "passes": false}]
All passes fields MUST be false. This is the Default-FAIL contract.
"""

def run_initializer(project_dir: Path) -> Path:
    plan_path = project_dir / "feature_list.json"

    if plan_path.exists():                              # ①
        raise FileExistsError(
            "Initializer has already run for this project. "
            "Delete feature_list.json to re-initialize."
        )

    client = _anthropic_client()
    if client is None:
        features = [dict(item) for item in _OFFLINE_FEATURES]
    else:
        response = client.messages.create(              # ②
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": INIT_PROMPT}],
        )
        raw = response.content[0].text
        features = json.loads(raw)                      # ③

    for f in features:
        assert not f["passes"], "Default-FAIL contract violated"

    plan_path.write_text(json.dumps(features, indent=2))

    progress = project_dir / "claude-progress.txt"     # ④
    progress.write_text(
        "## Done\n(none — initial session)\n\n"
        "## In Progress\n(none — initial session)\n\n"
        "## Next\n"
        + "\n".join(f"- {ft['description']}" for ft in features[:3])
        + "\n\n## Notes\nInitializer Agent ran. All features set to passes: false.\n"
    )

    subprocess.run(                                     # ⑤
        ["git", "add", "feature_list.json", "claude-progress.txt"],
        cwd=project_dir, check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init: Initializer Agent scaffolding"],
        cwd=project_dir, check=True,
    )
    return plan_path
