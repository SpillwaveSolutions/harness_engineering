"""Tests for listing 04-04-continuation-signal.

Exercises handle_stop_reason across every match arm:
end_turn, tool_use, max_tokens, model_context_window_exceeded,
refusal, pause_turn, and an unknown stop_reason.
"""

from __future__ import annotations

import pytest


def test_end_turn_returns_text(load_listing) -> None:
    """end_turn should return the extracted response text."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="The answer is 42.")
    result = m.handle_stop_reason("end_turn", response)
    assert result == "The answer is 42."


def test_tool_use_returns_continue(load_listing) -> None:
    """tool_use should return 'continue' to re-enter the loop."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    result = m.handle_stop_reason("tool_use", response)
    assert result == "continue"


def test_max_tokens_raises_token_limit_error(load_listing) -> None:
    """max_tokens should raise TokenLimitError."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    with pytest.raises(m.TokenLimitError):
        m.handle_stop_reason("max_tokens", response)


def test_context_window_raises_context_window_error(
    load_listing,
) -> None:
    """model_context_window_exceeded should raise ContextWindowError."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    with pytest.raises(m.ContextWindowError):
        m.handle_stop_reason("model_context_window_exceeded", response)


def test_refusal_raises_safety_refusal_error(load_listing) -> None:
    """refusal should raise SafetyRefusalError."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    with pytest.raises(m.SafetyRefusalError):
        m.handle_stop_reason("refusal", response)


def test_pause_turn_returns_continue(load_listing) -> None:
    """pause_turn should return 'continue' to resend the response."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    result = m.handle_stop_reason("pause_turn", response)
    assert result == "continue"


def test_unknown_stop_reason_raises(load_listing) -> None:
    """An unrecognised stop_reason should raise UnknownStopReasonError."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    with pytest.raises(m.UnknownStopReasonError):
        m.handle_stop_reason("something_new_in_2027", response)


def test_extract_text_from_fake_response(load_listing) -> None:
    """extract_text should return the text attribute of _FakeResponse."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="extracted!")
    assert m.extract_text(response) == "extracted!"


def test_extract_text_empty_when_no_text(load_listing) -> None:
    """extract_text should return empty string when text is empty."""
    m = load_listing("04-04-continuation-signal")
    response = m._FakeResponse(text="")
    assert m.extract_text(response) == ""
