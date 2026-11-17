from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic

CHARS_PER_TOKEN_HEURISTIC = 4  # Local estimate; count_tokens() is authoritative.


@dataclass
class ContextBudgetExceeded(Exception):
    current_tokens: int
    budget_tokens: int


SlotName = Literal[
    "system", "constraints", "history", "tool_output", "user_turn"
]

# Slot order encodes the U-shaped attention finding from §5.4:
# system + constraints get the high-attention head; user_turn gets
# the high-attention tail; history sits in the middle.
SLOT_ORDER: list[SlotName] = [
    "system",       # high attention: pinned facts
    "constraints",  # critical inviolables: re-injected every turn
    "history",      # compaction target: low attention by design
    "tool_output",  # most recent result: near the tail
    "user_turn",    # current user message: highest recency attention
]


@dataclass
class ContextSlot:
    name: SlotName
    messages: list[dict] = field(default_factory=list)


class OrderedContextAssembler:
    """Owns slot ordering. ContextManager owns budget; this owns position."""

    def __init__(self) -> None:
        self.slots: dict[SlotName, ContextSlot] = {
            name: ContextSlot(name=name) for name in SLOT_ORDER
        }

    def put(self, slot: SlotName, message: dict) -> None:
        self.slots[slot].messages.append(message)

    def assemble(self) -> list[dict]:
        out: list[dict] = []
        for name in SLOT_ORDER:
            out.extend(self.slots[name].messages)
        return out


class ContextManager:  # ①
    def __init__(
        self,
        client: anthropic.Anthropic,
        max_physical_tokens: int = 1_000_000,
        target_utilization: float = 0.70,
        max_tool_result_chars: int = 30_000,
        keep_recent_tool_results: int = 3,
    ) -> None:
        self.client = client
        self.budget = int(max_physical_tokens * target_utilization)  # ②
        self.max_tool_result_chars = max_tool_result_chars
        self.keep_recent_tool_results = keep_recent_tool_results

    def calculate_token_footprint(self, messages: list[dict]) -> int:  # ③
        """Fast local estimate via heuristic. Use count_tokens() for pre-flight."""
        total_chars = sum(
            len(str(m.get("content", ""))) for m in messages
        )
        return total_chars // CHARS_PER_TOKEN_HEURISTIC

    def enforce_result_budget(self, tool_name: str, raw_result: Any) -> Any:  # ④
        """
        PostToolUse boundary trim. Fires immediately after every tool call,
        before the result enters conversation history.
        """
        if isinstance(raw_result, str) and len(raw_result) > self.max_tool_result_chars:
            return (
                raw_result[: self.max_tool_result_chars]
                + f"\n[trimmed at boundary: {len(raw_result)} chars → "
                f"{self.max_tool_result_chars}]"
            )
        return raw_result

    def apply_tool_result_clearing(self, messages: list[dict]) -> int:  # ⑤
        """
        Surgical eviction: walk the message list, replace content of older
        tool results with a placeholder, preserve tool_use records.
        Returns the number of blocks cleared.
        """
        tool_result_indices = [
            i for i, m in enumerate(messages)
            if m.get("role") == "user"
            and isinstance(m.get("content"), list)
            and any(b.get("type") == "tool_result" for b in m["content"])
        ]
        to_clear = tool_result_indices[: -self.keep_recent_tool_results]
        cleared = 0
        for i in to_clear:
            messages[i]["content"] = "[tool result cleared for context budget]"
            cleared += 1
        return cleared

    def assemble_final_payload(  # ⑥
        self,
        system_prompt: str,
        persistent_facts: str,
        messages: list[dict],
    ) -> tuple[str, list[dict]]:
        """
        Two-pass assembly. Pass 1: static context (pinned, never compressed).
        Pass 2: dynamic history with budget enforcement cascade.
        """
        # Pass 1: static. Build the system prompt segment with pinned facts.
        static_system = system_prompt
        if persistent_facts:
            static_system = persistent_facts + "\n\n" + system_prompt

        # Pass 2: dynamic. Check budget; cascade if over.
        estimated = self.calculate_token_footprint(messages)
        if estimated > self.budget:
            cleared = self.apply_tool_result_clearing(messages)
            if cleared == 0:
                raise ContextBudgetExceeded(
                    current_tokens=estimated,
                    budget_tokens=self.budget,
                )
            # Re-estimate after clearing.
            estimated = self.calculate_token_footprint(messages)

        # Caller is responsible for triggering compaction or isolation
        # if ContextBudgetExceeded is raised and isolate policy applies.
        return static_system, messages


def main() -> None:
    manager = ContextManager(
        client=None,
        max_physical_tokens=1_000,
        target_utilization=0.5,
    )
    messages = [{"role": "user", "content": "Book a flight to Tokyo."}]
    system, payload = manager.assemble_final_payload(
        "You book travel.",
        "origin: SFO",
        messages,
    )
    print(manager.budget)
    print(system)
    print(payload[0]["content"])


if __name__ == "__main__":
    main()
