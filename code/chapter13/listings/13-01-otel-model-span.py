import os
import sys

import anthropic
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

# The exporter is attached on the first call, not at import, so a missing
# endpoint does not crash the module.
_configured = False


class _FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _FakeResponse:
    def __init__(self) -> None:
        self.usage = _FakeUsage(input_tokens=12, output_tokens=8)
        self.content = []


def get_tracer():
    """Attach an exporter once, then return the tracer."""
    global _configured
    if not _configured:
        current = trace.get_tracer_provider()
        if isinstance(current, trace.ProxyTracerProvider):
            provider = TracerProvider()
            endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
            if endpoint:
                provider.add_span_processor(
                    BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
                )
            else:
                print(
                    "OTEL_EXPORTER_OTLP_ENDPOINT is unset; "
                    "using an in-memory span exporter.",
                    file=sys.stderr,
                )
                provider.add_span_processor(
                    SimpleSpanProcessor(InMemorySpanExporter())
                )
            trace.set_tracer_provider(provider)
        _configured = True
    return trace.get_tracer("travel_booking_agent")


def call_model_with_span(
    messages: list[dict],
    conversation_id: str,
) -> anthropic.types.Message:
    # Span name follows the OTel GenAI convention:
    # "{gen_ai.operation.name} {gen_ai.request.model}"
    tracer = get_tracer()
    with tracer.start_as_current_span("chat claude-sonnet-4-6") as span:
        span.set_attribute("gen_ai.operation.name", "chat")         # ① Required
        span.set_attribute("gen_ai.provider.name", "anthropic")     # ② Required
        span.set_attribute(
            "gen_ai.request.model", "claude-sonnet-4-6"
        )  # ③ Conditionally Required
        span.set_attribute("gen_ai.conversation.id", conversation_id)  # ④ links turns

        if os.environ.get("ANTHROPIC_API_KEY"):
            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=messages,
            )
        else:
            print(
                "ANTHROPIC_API_KEY is unset; recording a fake model response.",
                file=sys.stderr,
            )
            response = _FakeResponse()

        # Attach usage AFTER the call — these become cost attributes in §13.3
        span.set_attribute(
            "gen_ai.usage.input_tokens", response.usage.input_tokens
        )
        span.set_attribute(
            "gen_ai.usage.output_tokens", response.usage.output_tokens
        )
        return response


def main() -> int:
    response = call_model_with_span(
        [{"role": "user", "content": "Find a flight to SFO"}],
        conversation_id="conv-offline",
    )
    print(
        f"input_tokens={response.usage.input_tokens} "
        f"output_tokens={response.usage.output_tokens}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
