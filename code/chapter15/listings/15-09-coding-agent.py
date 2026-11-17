import json
import os
import sys
from pathlib import Path

import anthropic

CODING_PROMPT_TEMPLATE = """
You are the Coding Agent for the travel-booking harness.

BOOT SEQUENCE (mandatory, in order):
1. Read claude-progress.txt — it is your handoff note from the last session
2. Run: git log --oneline -10
3. Run the project smoke test to confirm a clean baseline

YOUR TASK:
Implement exactly ONE incomplete feature from feature_list.json.
Select the first feature where "passes" is false and priority is high.

DISCIPLINE:
- Implement one feature completely before touching another
- Run the full test suite before marking passes: true
- Do not edit or delete any existing test
- End the session by writing a commit: "feat: <feature_description> (session N)"
- Update claude-progress.txt with what you did and what is next

INVIOLABLE: You cannot mark passes: true without running tests first.
"""

def run_coding_session(project_dir: Path, session_num: int) -> dict:
    plan_path = project_dir / "feature_list.json"
    if not plan_path.exists():                          # ①
        raise FileNotFoundError(
            "feature_list.json not found. Run the Initializer first."
        )

    features = json.loads(plan_path.read_text())
    incomplete = [f for f in features if not f["passes"]]
    if not incomplete:
        return {"status": "complete", "session": session_num}

    live = os.environ.get("HARNESS_LIVE_API") == "1"
    if not live or not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "offline: HARNESS_LIVE_API is not 1 or ANTHROPIC_API_KEY is unset",
            file=sys.stderr,
            flush=True,
        )
        return {
            "status": "offline",
            "session": session_num,
            "feature": incomplete[0].get("description", ""),
        }

    client = anthropic.Anthropic()
    prompt = CODING_PROMPT_TEMPLATE + f"\nSession number: {session_num}"

    response = client.messages.create(                  # ②
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    model_text = ""
    if getattr(response, "content", None):
        model_text = response.content[0].text
    return {
        "status": "session_complete",
        "session": session_num,
        "model_text": model_text,
    }
