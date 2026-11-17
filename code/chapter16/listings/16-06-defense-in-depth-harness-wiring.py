import sys
from pathlib import Path

_CHAPTER_ROOT = Path(__file__).resolve().parents[1]
if str(_CHAPTER_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHAPTER_ROOT))

from typing import Any

from harness.boundaries import (
    SourceChannel,
    enforce_context_length,
    filter_tool_output,
    validate_memory_write,
    verify_agent_card,
)
from opentelemetry import trace

tracer = trace.get_tracer("travel-booking.security")

class DefenseInDepthHarness:
    """Wires all four boundary defenses with per-boundary spans."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        tenant_id: str = "default",
    ) -> None:
        self.model = model
        self.tenant_id = tenant_id

    def on_user_input(self, text: str, session_id: str) -> str:
        with tracer.start_as_current_span(
            "security.context.length_check"
        ) as span:  # ①
            bounded = enforce_context_length(
                text, max_bytes=8192
            )
            span.set_attribute("input.bytes", len(text.encode()))
            span.set_attribute(
                "input.truncated", len(bounded) < len(text)
            )
        return bounded

    def on_tool_output(
        self, tool_name: str, raw_output: Any
    ) -> Any:
        with tracer.start_as_current_span(
            "security.tool.output_filter"
        ) as span:  # ②
            filtered = filter_tool_output(tool_name, raw_output)
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("filter.passed", True)
        return filtered

    def on_memory_write(
        self,
        content: str,
        session_id: str,
        source_channel: SourceChannel,
    ) -> None:
        with tracer.start_as_current_span(
            "security.memory.write_validator"
        ) as span:  # ③
            envelope = validate_memory_write(
                content,
                self.tenant_id,
                session_id,
                source_channel,
            )
            span.set_attribute(
                "memory.tenant_id", self.tenant_id
            )
            span.set_attribute(
                "memory.trust_score", envelope.trust_score
            )
            span.set_attribute(
                "memory.source_channel", source_channel.value
            )
        # Only reaches the store if validate_memory_write did not raise

    def on_a2a_peer_contact(
        self, agent_card: dict, public_key: Any
    ) -> None:
        with tracer.start_as_current_span(
            "security.a2a.card_verification"
        ) as span:  # ④
            verify_agent_card(agent_card, public_key)
            span.set_attribute(
                "a2a.agent_name",
                agent_card.get("name", "unknown"),
            )
            span.set_attribute("a2a.card_verified", True)
