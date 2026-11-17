from opentelemetry import trace

MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},  # per million tokens
}

tracer = trace.get_tracer("travel_booking_agent")

def record_cost(span: trace.Span, model: str, input_tokens: int, output_tokens: int) -> None:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    cost_usd = (
        (input_tokens * pricing["input"] / 1_000_000) +
        (output_tokens * pricing["output"] / 1_000_000)
    )
    span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
    span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
    span.set_attribute("harness.usage.cost_usd", cost_usd)  # custom; OTel has no cost_usd

def record_eval_verdict(
    span: trace.Span,
    name: str,
    score: float,
    label: str,          # low cardinality: "PASS" | "FAIL" | "NEEDS_REVIEW"
    explanation: str,
) -> None:
    span.set_attribute("gen_ai.evaluation.name", name)
    span.set_attribute("gen_ai.evaluation.score.value", score)
    span.set_attribute("gen_ai.evaluation.score.label", label)   # low cardinality required
    span.set_attribute("gen_ai.evaluation.explanation", explanation[:500])  # truncate PII risk
