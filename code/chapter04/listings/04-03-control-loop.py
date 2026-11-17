"""Listing 04-03: Five-step perceive-reason-plan-act-observe control loop.

Demonstrates the core harness control loop against a stubbed Anthropic client
so the logic is testable without a live API call.

Chapter 4, Section 4.3 -- The agent control loop.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Minimal stubs that mirror the Anthropic SDK surface used by the loop.
# These let the listing run and be tested without a live Anthropic account.
# ---------------------------------------------------------------------------

class _FakeBlock:
    """One content block in a fake model response."""

    def __init__(
        self,
        block_type: str,
        text: str = "",
        tool_name: str = "",
        tool_id: str = "",
        tool_input: dict | None = None,
    ) -> None:
        self.type = block_type
        self.text = text
        self.name = tool_name
        self.id = tool_id
        self.input = tool_input or {}


class _FakeResponse:
    """Minimal stand-in for anthropic.types.Message."""

    def __init__(
        self,
        stop_reason: str,
        content: list[_FakeBlock],
    ) -> None:
        self.stop_reason = stop_reason
        self.content = content


class _FakeMessages:
    """Callable that returns a pre-configured sequence of responses."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self._index = 0

    def create(self, **_kwargs: Any) -> _FakeResponse:
        if self._index >= len(self._responses):
            raise RuntimeError("No more fake responses configured.")
        resp = self._responses[self._index]
        self._index += 1
        return resp


class _FakeClient:
    """Minimal stand-in for anthropic.Anthropic()."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _FakeMessages(responses)


# ---------------------------------------------------------------------------
# The runnable control loop (matches the prose representative block).
# ---------------------------------------------------------------------------

def run_control_loop(
    client: Any,
    system: str,
    initial_user_message: str,
    tools: list[dict],
    tool_dispatch: dict[str, Any],
    max_turns: int = 20,
) -> str:
    """Five-step perceive-reason-plan-act-observe control loop.

    Args:
        client: Anthropic client (or compatible stub).
        system: System prompt string.
        initial_user_message: First user turn.
        tools: Tool schema list passed to the model.
        tool_dispatch: Maps tool name -> callable.
        max_turns: Hard upper bound on loop iterations.

    Returns:
        The model's final text response.

    Raises:
        RuntimeError: When a resource limit is hit or max_turns exceeded.
    """
    messages: list[dict] = []
    turns: int = 0

    # Perceive: assemble initial input ①
    messages.append({"role": "user", "content": initial_user_message})

    while turns < max_turns:
        # Reason: model call (data plane) ②
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )

        # Observe the continuation signal (control plane reads data plane) ③
        stop_reason = response.stop_reason

        if stop_reason == "end_turn":
            return response.content[0].text  # natural completion

        # [PLAN-MODE GATE — §4.6 insertion point]
        # In plan mode, the harness restricts tool access to read-only here,
        # before dispatching any tool call. While the gate is active the model
        # may only call read-only tools (e.g. file reads, web lookups) so it
        # can propose a sequence of actions without executing irreversible ones.
        # Once the plan is approved (by a human reviewer or a policy check),
        # the harness clears the gate and re-enters this block in execution
        # mode, allowing the full tool_dispatch to run.
        # See Section 4.6 for the decision rule on when plan mode is warranted.

        if stop_reason == "tool_use":
            # Act: dispatch tool calls (data plane) ④
            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "tool_use":
                    # Pre-hook: validate before execution
                    result = tool_dispatch[block.name](**block.input)
                    # Post-hook: validate result before returning
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )

            # Perceive next turn: append tool results to message history ⑤
            messages.append(
                {"role": "assistant", "content": response.content}
            )
            messages.append({"role": "user", "content": tool_results})
            turns += 1
            continue

        if stop_reason in (
            "max_tokens",
            "model_context_window_exceeded",
        ):
            raise RuntimeError(
                f"Resource limit hit: {stop_reason}"
            )

    raise RuntimeError("max_turns exceeded without completion")


# ---------------------------------------------------------------------------
# Annotations (load-bearing lines)
# ---------------------------------------------------------------------------
# ① Perceive step: the harness assembles the initial context before the
#   first model call.
# ② Reason step: the model call is the sole data-plane operation here.
#   The harness does not interpret the response at this point.
# ③ Observe the continuation signal: stop_reason is the data plane's
#   structured output to the control plane.
# ④ Act step: the harness dispatches each tool call; pre- and post-hooks
#   attach here in production.
# ⑤ Perceive next turn: tool results feed into the next loop iteration as
#   structured context, not raw text.


if __name__ == "__main__":
    # Demo: single end_turn response, no tools required.
    fake_client = _FakeClient(
        responses=[
            _FakeResponse(
                stop_reason="end_turn",
                content=[_FakeBlock("text", text="Hello from the loop.")],
            )
        ]
    )
    output = run_control_loop(
        client=fake_client,
        system="You are a demo agent.",
        initial_user_message="Say hello.",
        tools=[],
        tool_dispatch={},
    )
    print(f"Loop result: {output}")
