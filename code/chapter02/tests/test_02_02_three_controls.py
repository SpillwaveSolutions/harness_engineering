"""Tests for listing 02-02-three-controls (§2.2).

Pins the three self-contained controls the harnessed agent adds on top of the
naked loop from §2.1:

  - schema validation   — validate_plan_step rejects malformed / unknown tools
  - token-budget memory — trim_history keeps history under MAX_HISTORY_TOKENS
  - the token estimator — count_tokens_approx the trimmer depends on

run_harnessed stays offline unless HARNESS_LIVE_API=1 and
ANTHROPIC_API_KEY are both set. The offline reply includes the user
text and does not construct a client.
"""

from __future__ import annotations

# --- schema validation (validate_plan_step) -------------------------------

def test_valid_search_flights_passes(load_listing):
    """§2.2: a well-formed search_flights plan step validates clean."""
    listing = load_listing("02-02-three-controls")

    ok, reason = listing.validate_plan_step(
        "search_flights",
        {"origin": "SFO", "destination": "JFK", "date": "2099-12-31"},
    )

    assert ok is True
    assert reason == ""


def test_valid_book_flight_passes(load_listing):
    """§2.2: book_flight has its own arg model — a valid step validates clean."""
    listing = load_listing("02-02-three-controls")

    ok, reason = listing.validate_plan_step(
        "book_flight",
        {"flight_id": "AA42", "passenger_name": "Ada Lovelace"},
    )

    assert ok is True
    assert reason == ""


def test_malformed_args_are_rejected(load_listing):
    """§2.2: a 2-letter origin violates the 3-char IATA field and is refused."""
    listing = load_listing("02-02-three-controls")

    ok, reason = listing.validate_plan_step(
        "search_flights",
        {"origin": "SF", "destination": "JFK", "date": "2099-12-31"},
    )

    assert ok is False
    assert reason  # non-empty: carries the validation error back to the model


def test_past_date_is_rejected(load_listing):
    """§2.2: the must_not_be_past validator blocks travel dates in the past."""
    listing = load_listing("02-02-three-controls")

    ok, reason = listing.validate_plan_step(
        "search_flights",
        {"origin": "SFO", "destination": "JFK", "date": "2000-01-01"},
    )

    assert ok is False
    assert "past" in reason


def test_unknown_tool_is_rejected(load_listing):
    """§2.2: a tool name with no arg model fails before any schema check."""
    listing = load_listing("02-02-three-controls")

    ok, reason = listing.validate_plan_step("teleport", {})

    assert ok is False
    assert reason == "unknown tool: teleport"


# --- token-budget memory (count_tokens_approx + trim_history) -------------

def test_count_tokens_approx_uses_four_chars_per_token(load_listing):
    """§2.2: the estimator is the cheap 1-token-per-4-chars heuristic."""
    listing = load_listing("02-02-three-controls")

    tokens = listing.count_tokens_approx([{"role": "user", "content": "x" * 40}])

    assert tokens == 10  # 40 chars // 4


def test_trim_history_drops_oldest_until_under_budget(load_listing):
    """§2.2: an over-budget history is trimmed back under MAX_HISTORY_TOKENS."""
    listing = load_listing("02-02-three-controls")
    # 10 messages * 4000 chars = 10000 tokens, well over the 4000 cap.
    messages = [{"role": "user", "content": "x" * 4000} for _ in range(10)]

    trimmed = listing.trim_history(messages)

    assert len(trimmed) < len(messages)
    assert listing.count_tokens_approx(trimmed) <= listing.MAX_HISTORY_TOKENS


def test_trim_history_preserves_leading_system_message(load_listing):
    """§2.2: the system prompt at index 0 survives trimming — only the
    conversation turns after it are evicted."""
    listing = load_listing("02-02-three-controls")
    messages = [{"role": "system", "content": "you are a travel agent"}]
    messages += [{"role": "user", "content": "x" * 4000} for _ in range(10)]

    trimmed = listing.trim_history(messages)

    assert trimmed[0]["role"] == "system"
    assert listing.count_tokens_approx(trimmed) <= listing.MAX_HISTORY_TOKENS


def test_trim_history_keeps_tool_pairs_intact(load_listing):
    """§2.2: trimming a history that contains tool pairs must never
    orphan a tool_result from its tool_use. Anthropic rejects a
    tool_result that is not immediately preceded by the assistant
    message carrying the matching tool_use."""
    listing = load_listing("02-02-three-controls")
    big = "x" * 20000  # ~5000 tokens/turn, forces trimming into a pair
    messages = [
        {"role": "user", "content": "book me a flight " + big},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1",
             "name": "search_flights", "input": {}}]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1",
             "content": big}]},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t2",
             "name": "book_flight", "input": {}}]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t2",
             "content": "confirmed"}]},
    ]

    trimmed = listing.trim_history(messages)

    # Trimming actually happened.
    assert len(trimmed) < len(messages)
    # Every surviving tool_result is immediately preceded by an
    # assistant message that carries a tool_use — no orphans.
    for i, msg in enumerate(trimmed):
        if listing._has_tool_result(msg):
            assert i > 0
            prev = trimmed[i - 1]
            assert prev["role"] == "assistant"
            assert any(
                isinstance(b, dict) and b.get("type") == "tool_use"
                for b in prev["content"]
            )
    assert (
        listing.count_tokens_approx(trimmed)
        <= listing.MAX_HISTORY_TOKENS
    )


# --- dispatch failure handling (execute_tool_call) ------------------------

def _in_memory_exporter():
    """Install an SDK tracer provider with an in-memory exporter so the
    test can inspect the spans execute_tool_call opens and closes."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


def test_raising_tool_marks_span_error_closes_and_is_error(load_listing):
    """§2.2: a tool that raises must still (1) close its span, (2) mark
    it ERROR, and (3) feed the failure back as a tool_result with
    is_error=True — the same shape the validator uses on rejection."""
    exporter = _in_memory_exporter()
    listing = load_listing("02-02-three-controls")

    def boom(name: str, args: dict) -> str:
        raise ValueError("Seat unavailable on flight AA1234")

    listing.dispatch = boom  # tool raises inside the span
    exporter.clear()

    result = listing.execute_tool_call(
        "toolu_1", "book_flight",
        {"flight_id": "AA1234", "passenger_name": "Ada"},
    )

    block = result["content"][0]
    assert block["type"] == "tool_result"
    assert block["is_error"] is True
    assert "Seat unavailable" in block["content"]

    spans = [
        s for s in exporter.get_finished_spans()
        if s.name == "tool.book_flight"
    ]
    assert len(spans) == 1  # span was closed (exported)
    span = spans[0]
    assert span.end_time is not None
    assert span.status.status_code.name == "ERROR"
    assert span.attributes["tool.success"] is False


def test_successful_tool_marks_span_ok_no_is_error(load_listing):
    """§2.2: the happy path sets tool.success=True and returns a plain
    tool_result with no is_error flag."""
    exporter = _in_memory_exporter()
    listing = load_listing("02-02-three-controls")
    exporter.clear()

    result = listing.execute_tool_call(
        "toolu_2", "search_flights",
        {"origin": "SFO", "destination": "JFK", "date": "2099-12-31"},
    )

    block = result["content"][0]
    assert "is_error" not in block
    spans = [
        s for s in exporter.get_finished_spans()
        if s.name == "tool.search_flights"
    ]
    assert len(spans) == 1
    assert spans[0].attributes["tool.success"] is True


def test_tools_cover_search_and_book(load_listing):
    """TOOLS names the two travel tools the harnessed loop can call."""
    listing = load_listing("02-02-three-controls")
    names = [tool["name"] for tool in listing.TOOLS]
    assert names == ["search_flights", "book_flight"]


def test_dispatch_returns_short_results(load_listing):
    """dispatch returns a short string for both travel tools."""
    listing = load_listing("02-02-three-controls")
    search = listing.dispatch("search_flights", {})
    booked = listing.dispatch("book_flight", {"flight_id": "AA42"})
    assert "AA42" in search
    assert booked == '{"status": "confirmed", "id": "AA42"}'


def test_run_harnessed_offline_echoes_user_text(
    load_listing, monkeypatch, capsys
):
    """Missing live settings return the user text and skip the client."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    listing = load_listing("02-02-three-controls")

    class Boom:
        def __init__(self, *args, **kwargs):
            raise AssertionError("client constructed")

    monkeypatch.setattr(listing.anthropic, "Anthropic", Boom)
    reply = listing.run_harnessed("Need a flight to Oslo")
    assert reply == "offline reply: Need a flight to Oslo"
    err = capsys.readouterr().err
    assert "HARNESS_LIVE_API=1" in err
    assert "ANTHROPIC_API_KEY" in err
