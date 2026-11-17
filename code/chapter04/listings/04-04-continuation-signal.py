"""Listing 04-04: Read the continuation signal and dispatch control flow.

Each match arm maps one stop_reason value to the correct harness action.
Helper classes (TokenLimitError, ContextWindowError, SafetyRefusalError,
UnknownStopReasonError) are defined here so the module is self-contained
and importable without the live Anthropic SDK.

Chapter 4, Section 4.4 -- The continuation signal.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Sentinel exceptions -- one per error arm in handle_stop_reason.
# ---------------------------------------------------------------------------

class TokenLimitError(RuntimeError):
    """Raised when the model response was truncated at max_tokens."""


class ContextWindowError(RuntimeError):
    """Raised when the model's context window is full."""


class SafetyRefusalError(RuntimeError):
    """Raised when the model refused due to a safety policy."""


class UnknownStopReasonError(ValueError):
    """Raised when stop_reason carries an unrecognised value."""


# ---------------------------------------------------------------------------
# Minimal response stub so tests stay off the network.
# ---------------------------------------------------------------------------

class _FakeResponse:
    """Stand-in for anthropic.types.Message with a text attribute."""

    def __init__(self, text: str = "") -> None:
        self.text = text


# ---------------------------------------------------------------------------
# Helper used inside handle_stop_reason.
# ---------------------------------------------------------------------------

def extract_text(response: Any) -> str:
    """Extract the plain text from a model response object.

    Works with both the real Anthropic SDK Message and the _FakeResponse stub.
    Returns an empty string when no text is found.
    """
    # Real SDK: response.content is a list of blocks.
    if hasattr(response, "content") and isinstance(response.content, list):
        parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "".join(parts)
    # Stub shortcut.
    if hasattr(response, "text"):
        return response.text
    return ""


# ---------------------------------------------------------------------------
# The continuation-signal dispatcher (matches the prose representative block).
# ---------------------------------------------------------------------------

def handle_stop_reason(  # ①
    stop_reason: str,
    response: Any,
) -> str:
    """Read the continuation signal and dispatch control flow.

    Args:
        stop_reason: The ``stop_reason`` string from the model response.
        response: The full model response object (used to extract text on
            ``end_turn``).

    Returns:
        ``"continue"`` when the loop should keep running, or the extracted
        response text when the model finished naturally.

    Raises:
        TokenLimitError: When stop_reason is ``"max_tokens"``.
        ContextWindowError: When stop_reason is
            ``"model_context_window_exceeded"``.
        SafetyRefusalError: When stop_reason is ``"refusal"``.
        UnknownStopReasonError: When stop_reason is not a known value.
    """
    match stop_reason:
        case "end_turn":
            # Natural completion: the model finished its response. ②
            return extract_text(response)

        case "tool_use":
            # Tool call required: dispatch and loop. ③
            # The harness owns the loop; the model just asked for a tool.
            return "continue"

        case "max_tokens":
            # Token limit hit. Options: compact context, raise, or escalate.
            raise TokenLimitError(
                "Response truncated at max_tokens"
            )  # ④

        case "model_context_window_exceeded":
            # Context window full. Compact or truncate before next call.
            raise ContextWindowError(
                "Context window exceeded; compact before retry"
            )  # ⑤

        case "refusal":
            # Safety refusal. Log and surface to the caller.
            raise SafetyRefusalError(
                "Model refused: safety policy"
            )  # ⑥

        case "pause_turn":
            # Server-side iteration limit. Continue by re-sending as-is.
            return "continue"  # ⑦

        case _:
            raise UnknownStopReasonError(
                f"Unhandled stop_reason: {stop_reason}"
            )  # ⑧


# ---------------------------------------------------------------------------
# Annotations (load-bearing lines, matches prose numbering)
# ---------------------------------------------------------------------------
# ① Function signature: takes the raw stop_reason string plus the full
#   response so the end_turn arm can extract text without a second call.
# ② end_turn: natural completion; extract and return the model's text.
# ③ tool_use: return the sentinel "continue" so the caller re-enters the
#   loop and dispatches the tool.
# ④ max_tokens: the per-call token limit was reached; raise so the harness
#   can decide whether to compact context or surface the error.
# ⑤ model_context_window_exceeded: the entire context window is full; the
#   harness must compact or truncate before the next call.
# ⑥ refusal: a safety policy blocked the response; surface it explicitly
#   rather than silently returning empty text.
# ⑦ pause_turn: the server-side sampling loop hit its per-request iteration
#   cap; resend the response as-is to continue.
# ⑧ Catch-all: any future stop_reason values become explicit errors, not
#   silent failures.


def main() -> None:
    fake_response = _FakeResponse(text="The answer is 42.")
    end = handle_stop_reason("end_turn", fake_response)
    print(f"end_turn result: {end}")
    continued = handle_stop_reason("tool_use", fake_response)
    print(f"tool_use result: {continued}")


if __name__ == "__main__":
    main()
