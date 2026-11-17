import os
import sys
from typing import ClassVar

from opentelemetry import trace
from opentelemetry.trace import SpanKind

tracer = trace.get_tracer("travel_booking_agent")


class _Usage:
    input_tokens = 16
    output_tokens = 8


class _ToolUse:
    type = "tool_use"
    name = "search_flights"
    id = "toolu_offline"
    input: ClassVar[dict] = {"destination": "SFO"}


class _OfflineModelResponse:
    def __init__(self) -> None:
        self.usage = _Usage()
        self.content = [_ToolUse()]


def call_model(messages: list[dict]):
    """Return a model response. No network call when the key is unset."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is unset; returning an offline model response.",
            file=sys.stderr,
        )
        return _OfflineModelResponse()
    import anthropic

    client = anthropic.Anthropic()
    return client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=messages,
    )


def dispatch_tool(name: str, arguments: dict) -> dict:
    return {"status": "ok", "tool": name, "arguments": arguments}


def run_booking_step(conversation_id: str, messages: list[dict]) -> dict:
    # Parent: invoke_agent wraps one complete agent turn
    with tracer.start_as_current_span(
        "invoke_agent travel_booking_agent",
        kind=SpanKind.CLIENT,
    ) as agent_span:
        agent_span.set_attribute("gen_ai.agent.name", "travel_booking_agent")
        agent_span.set_attribute("gen_ai.agent.id", "tba-v2.1.0")
        agent_span.set_attribute("gen_ai.conversation.id", conversation_id)

        # Child: model call
        with tracer.start_as_current_span("chat claude-sonnet-4-6") as model_span:
            model_span.set_attribute("gen_ai.operation.name", "chat")
            model_span.set_attribute("gen_ai.provider.name", "anthropic")
            model_span.set_attribute("gen_ai.request.model", "claude-sonnet-4-6")
            response = call_model(messages)
            model_span.set_attribute(
                "gen_ai.usage.input_tokens", response.usage.input_tokens
            )
            model_span.set_attribute(
                "gen_ai.usage.output_tokens", response.usage.output_tokens
            )

        # Child: tool call
        tool_results: list[dict] = []
        for tool_use in response.content:
            if tool_use.type == "tool_use":
                with tracer.start_as_current_span(
                    f"execute_tool {tool_use.name}"
                ) as tool_span:
                    tool_span.set_attribute("gen_ai.tool.name", tool_use.name)
                    tool_span.set_attribute("gen_ai.tool.call.id", tool_use.id)
                    tool_span.set_attribute(
                        "gen_ai.tool.call.arguments", str(tool_use.input)
                    )
                    result = dispatch_tool(tool_use.name, tool_use.input)
                    tool_span.set_attribute(
                        "gen_ai.tool.call.result", str(result)
                    )
                    if result.get("status") == "error":
                        tool_span.set_attribute(
                            "error.type", result.get("code", "unknown")
                        )
                    tool_results.append(result)
        return {
            "conversation_id": conversation_id,
            "status": "ok",
            "tools": tool_results,
        }


def main() -> int:
    result = run_booking_step(
        "conv-offline",
        [{"role": "user", "content": "Find a flight to SFO"}],
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
