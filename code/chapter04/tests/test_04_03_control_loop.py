"""Tests for listing 04-03-control-loop.

Exercises the run_control_loop function across all stop_reason branches:
end_turn (natural completion), tool_use (dispatch and loop), max_tokens,
and model_context_window_exceeded.

All responses are stubbed -- no live Anthropic API calls are made.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Test: end_turn branch returns model text immediately.
# ---------------------------------------------------------------------------

def test_end_turn_returns_text(load_listing) -> None:
    """end_turn stop_reason should return the model's text."""
    m = load_listing("04-03-control-loop")

    response = m._FakeResponse(
        stop_reason="end_turn",
        content=[m._FakeBlock("text", text="Hello, world!")],
    )
    client = m._FakeClient([response])

    result = m.run_control_loop(
        client=client,
        system="You are a helpful assistant.",
        initial_user_message="Say hello.",
        tools=[],
        tool_dispatch={},
    )
    assert result == "Hello, world!"


# ---------------------------------------------------------------------------
# Test: tool_use branch dispatches the tool and loops to end_turn.
# ---------------------------------------------------------------------------

def test_tool_use_dispatches_and_continues(load_listing) -> None:
    """tool_use should call the dispatch function and then loop."""
    m = load_listing("04-03-control-loop")

    tool_calls: list[dict] = []

    def echo_tool(**kwargs):
        tool_calls.append(kwargs)
        return "tool_result_42"

    tool_response = m._FakeResponse(
        stop_reason="tool_use",
        content=[
            m._FakeBlock(
                "tool_use",
                tool_name="echo",
                tool_id="tid-1",
                tool_input={"value": "ping"},
            )
        ],
    )
    end_response = m._FakeResponse(
        stop_reason="end_turn",
        content=[m._FakeBlock("text", text="Done after tool.")],
    )
    client = m._FakeClient([tool_response, end_response])

    result = m.run_control_loop(
        client=client,
        system="Agent",
        initial_user_message="Use the echo tool.",
        tools=[],
        tool_dispatch={"echo": echo_tool},
    )
    assert result == "Done after tool."
    assert tool_calls == [{"value": "ping"}]


# ---------------------------------------------------------------------------
# Test: max_tokens raises RuntimeError with the correct message.
# ---------------------------------------------------------------------------

def test_max_tokens_raises(load_listing) -> None:
    """max_tokens stop_reason should raise RuntimeError."""
    m = load_listing("04-03-control-loop")

    response = m._FakeResponse(stop_reason="max_tokens", content=[])
    client = m._FakeClient([response])

    with pytest.raises(RuntimeError, match="max_tokens"):
        m.run_control_loop(
            client=client,
            system="Agent",
            initial_user_message="Trigger token limit.",
            tools=[],
            tool_dispatch={},
        )


# ---------------------------------------------------------------------------
# Test: model_context_window_exceeded raises RuntimeError.
# ---------------------------------------------------------------------------

def test_context_window_exceeded_raises(load_listing) -> None:
    """model_context_window_exceeded stop_reason should raise RuntimeError."""
    m = load_listing("04-03-control-loop")

    response = m._FakeResponse(
        stop_reason="model_context_window_exceeded", content=[]
    )
    client = m._FakeClient([response])

    with pytest.raises(
        RuntimeError, match="model_context_window_exceeded"
    ):
        m.run_control_loop(
            client=client,
            system="Agent",
            initial_user_message="Fill the context.",
            tools=[],
            tool_dispatch={},
        )


# ---------------------------------------------------------------------------
# Test: exceeding max_turns raises RuntimeError.
# ---------------------------------------------------------------------------

def test_max_turns_exceeded_raises(load_listing) -> None:
    """Loop should raise RuntimeError when max_turns is exceeded."""
    m = load_listing("04-03-control-loop")

    # Every response is tool_use so the loop never hits end_turn.
    repeating_tool = m._FakeResponse(
        stop_reason="tool_use",
        content=[
            m._FakeBlock(
                "tool_use",
                tool_name="noop",
                tool_id="t1",
                tool_input={},
            )
        ],
    )
    # Provide enough responses so we don't exhaust the fake client first.
    client = m._FakeClient([repeating_tool] * 5)

    with pytest.raises(RuntimeError, match="max_turns exceeded"):
        m.run_control_loop(
            client=client,
            system="Agent",
            initial_user_message="Loop forever.",
            tools=[],
            tool_dispatch={"noop": lambda: "ok"},
            max_turns=3,
        )
