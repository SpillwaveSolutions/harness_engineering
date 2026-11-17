import json
import sys

from a2a.client import Client
from a2a.types import SendMessageRequest, TaskState


class InputRequired(Exception):
    """The remote task is waiting for another user message."""


class AuthRequired(Exception):
    """The remote task is waiting for out-of-band authentication."""


class TaskFailed(Exception):
    """The remote task ended in the failed state."""


_TERMINAL = {
    TaskState.TASK_STATE_COMPLETED,
    TaskState.TASK_STATE_FAILED,
    TaskState.TASK_STATE_CANCELED,
    TaskState.TASK_STATE_REJECTED,
}


async def _open_stream(client: Client, message):
    """Yield StreamResponse events. A client without send_message stays offline."""
    send = getattr(client, "send_message", None)
    if send is None:
        print(
            "A2A stream is offline; no message was sent.",
            file=sys.stderr,
        )
        if False:
            yield None
        return
    request = (
        message
        if isinstance(message, SendMessageRequest)
        else SendMessageRequest(message=message)
    )
    async for event in send(request):
        yield event


async def stream_loyalty_task(client: Client, message) -> dict:
    artifact_chunks = {}

    async for event in _open_stream(client, message):
        kind = event.WhichOneof("payload")
        if kind == "status_update":
            update = event.status_update
            state = update.status.state

            if state == TaskState.TASK_STATE_INPUT_REQUIRED:
                raise InputRequired(update.status.message)

            if state == TaskState.TASK_STATE_AUTH_REQUIRED:
                raise AuthRequired(update.status.message)

            if state == TaskState.TASK_STATE_FAILED:
                raise TaskFailed(update.status.message)

            if state in _TERMINAL:
                break  # ① stream complete

        elif kind == "artifact_update":
            update = event.artifact_update
            artifact_id = update.artifact.artifact_id
            if update.append:
                artifact_chunks.setdefault(artifact_id, [])
                artifact_chunks[artifact_id].extend(update.artifact.parts)
            if update.last_chunk:
                pass  # ② commit this artifact to durable storage

    return artifact_chunks


def main() -> int:
    print(json.dumps({"status": "offline", "events": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
