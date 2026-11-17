from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import Any


@dataclass
class HarnessComponents:
    """The seven core harness components. Every production harness has all seven."""
    context_manager: Any          # ① Perception: assembles what enters the window
    memory: Any                   # Memory: working, semantic, persistent tiers
    validators: list[Callable]    # ② Action: pre- and post-call validation hooks
    tools: dict[str, Callable]    # ② Action: named capability functions
    observability: Any            # ③ Cross-cutting: spans, traces, cost
    recovery: Any                 # ③ Cross-cutting: retry, fallback, escalation
    coordination: Any | None   # Collaboration: handoff and shared state


def main() -> None:
    components = HarnessComponents(
        context_manager="context",
        memory={},
        validators=[],
        tools={},
        observability="spans",
        recovery="retry",
        coordination=None,
    )
    print(", ".join(item.name for item in fields(components)))
    print(components.observability)


if __name__ == "__main__":
    main()
