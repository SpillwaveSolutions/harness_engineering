import json
import os
import sys

import modal
from deepagents import create_deep_agent
from langchain_anthropic import ChatAnthropic


def build_sandbox_agent() -> dict:
    """Launch a sandbox-backed agent, or an offline stand-in.

    ``MODAL_TOKEN_ID`` gates the live Modal lookup. Without it this
    returns immediately and does not call Modal.
    """
    if not os.environ.get("MODAL_TOKEN_ID"):
        print(
            "MODAL_TOKEN_ID is unset; sandbox agent is offline.",
            file=sys.stderr,
        )
        return {"status": "offline"}

    # ① Launch a gVisor-backed sandbox scoped to this agent session.
    # The sandbox object is the deepagents backend. There is no
    # langchain-modal package to wrap it.
    app = modal.App.lookup("travel-booking-agent")
    modal_sandbox = modal.Sandbox.create(app=app)
    try:
        agent = create_deep_agent(
            model=ChatAnthropic(model="claude-sonnet-4-6"),
            tools=[],
            system_prompt=(
                "You are a travel booking assistant with sandbox access."
            ),
            backend=modal_sandbox,
        )
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": (
                    "Run the booking consolidation script "
                    "and show me the results"
                ),
            }]
        })
    finally:
        # ② Always terminate the sandbox (leaked sandboxes accumulate cost)
        modal_sandbox.terminate()
    if isinstance(result, dict):
        return result
    return {"status": "ok", "result": result}


def main() -> int:
    print(json.dumps(build_sandbox_agent()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
