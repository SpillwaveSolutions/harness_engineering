"""Two-plane sketch: policy in the control plane, execution in the data plane.

Offline methods return deterministic results. Nothing here calls the network.
"""

from __future__ import annotations


class _ModelResponse:
    """Structured model result the control plane can read."""

    def __init__(self, stop_reason: str, content: str) -> None:
        self.stop_reason = stop_reason
        self.content = content


def _message_text(messages) -> str:
    if isinstance(messages, str):
        return messages
    if not isinstance(messages, list):
        return str(messages)
    parts: list[str] = []
    for item in messages:
        if isinstance(item, dict):
            parts.append(str(item.get("content", "")))
        else:
            parts.append(str(item))
    return " ".join(parts)


# DATA PLANE — pure execution, no policy.
class DataPlane:
    def __init__(self) -> None:
        self.memory: dict[str, object] = {}

    def call_model(self, messages, tools):  # ①
        del tools
        text = _message_text(messages)
        return _ModelResponse("end_turn", f"offline reply: {text}")

    def invoke_tool(self, name, inputs):
        return f"invoked {name} {inputs!r}"

    def write_memory(self, key, value):
        self.memory[str(key)] = value
        return value


# CONTROL PLANE — all policy decisions.
class ControlPlane:
    def __init__(self, dp: DataPlane) -> None:  # ②
        self.dp = dp
        self.turns = 0

    def should_stop(self) -> bool:  # ③
        return self.turns >= 1

    def escalate(self) -> str:
        return "escalated"

    def run(self, goal: str) -> str:
        while True:
            if self.should_stop():
                return self.escalate()
            response = self.dp.call_model(  # ④
                [{"role": "user", "content": goal}],
                [],
            )
            self.turns += 1
            if response.stop_reason == "end_turn":
                return response.content
            # policy checks (permissions, no-progress, budget) here


def main() -> None:
    print(ControlPlane(DataPlane()).run("Book a flight to Tokyo."))


if __name__ == "__main__":
    main()
