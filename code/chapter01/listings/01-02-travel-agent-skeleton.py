"""Travel-booking agent skeleton from Chapter 1 §1.7.

Starts with none of the six harness capabilities. Each TODO names a capability
that gets added in a later chapter. The skeleton is intentionally fragile so
the reader can watch what breaks when the harness is missing, then see how
each capability addresses the failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TravelBookingAgent:
    model_client: Any
    session_id: str = ""
    turn_history: list = field(default_factory=list)

    def run(self, user_message: str) -> str:
        # TODO context assembly:  shape what enters the context window
        # TODO tool contracts:    validate tool calls before executing
        # TODO memory:            load and save session memory
        # TODO observability:     emit spans for every decision
        # TODO recovery:          retry and escalate on failure
        # TODO orchestration:     coordinate with sub-agents
        return self.model_client.complete(user_message)


def main() -> None:
    class _DemoClient:
        def complete(self, message: str) -> str:
            return "I have booked your trip to Paris."

    agent = TravelBookingAgent(model_client=_DemoClient())
    print(agent.run("Rebook this customer"))


if __name__ == "__main__":
    main()
