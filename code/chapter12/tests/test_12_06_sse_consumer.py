"""Tests for listing 12-06-sse-consumer.

Depends on a2a-sdk (A2AClient, TaskState, TaskStatusUpdateEvent,
TaskArtifactUpdateEvent). Skips gracefully if a2a-sdk is not installed.

Structural claim from §12.6: the listing exports an async function
`stream_loyalty_task` that accepts an A2AClient and a message, streams
events, and returns a dict of artifact chunks.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-06-sse-consumer")
    assert module is not None


def test_stream_loyalty_task_is_callable(load_listing):
    module = load_listing("12-06-sse-consumer")
    assert callable(module.stream_loyalty_task)


async def test_stream_raises_input_required(load_listing):
    module = load_listing("12-06-sse-consumer")
    from a2a.types import (
        Message,
        Part,
        Role,
        StreamResponse,
        TaskState,
        TaskStatus,
        TaskStatusUpdateEvent,
    )

    event = StreamResponse(
        status_update=TaskStatusUpdateEvent(
            task_id="task-1",
            status=TaskStatus(
                state=TaskState.TASK_STATE_INPUT_REQUIRED,
                message=Message(
                    message_id="q",
                    role=Role.ROLE_AGENT,
                    parts=[Part(text="which dates?")],
                ),
            ),
        )
    )

    class Client:
        async def send_message(self, request):
            del request
            yield event

    try:
        await module.stream_loyalty_task(Client(), message=Message(
            message_id="m", role=Role.ROLE_USER, parts=[Part(text="hi")]
        ))
    except module.InputRequired as exc:
        assert "which dates?" in str(exc)
    else:
        raise AssertionError("input-required must raise InputRequired")


async def test_stream_offline_without_client_method(load_listing):
    module = load_listing("12-06-sse-consumer")
    chunks = await module.stream_loyalty_task(object(), message={})
    assert chunks == {}
