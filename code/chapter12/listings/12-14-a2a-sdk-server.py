import json
import os
import sys

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Artifact,
    Part,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from anthropic import Anthropic
from google.protobuf.struct_pb2 import Struct, Value


def data_part(payload: dict) -> Part:
    struct = Struct()
    struct.update(payload)
    return Part(data=Value(struct_value=struct))


class HotelLoyaltyExecutor(AgentExecutor):
    """Minimal A2A executor: bring your own cognitive loop."""

    def __init__(self):
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.llm = Anthropic()
        else:
            print(
                "ANTHROPIC_API_KEY is unset; loyalty lookup stays offline.",
                file=sys.stderr,
            )
            self.llm = None

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> dict:
        task_id = context.task_id or "offline"
        context_id = context.context_id or "offline"
        await event_queue.enqueue_event(                    # ①
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        account_id = _account_id(context)
        payload = {
            "accountId": account_id,
            "status": "platinum",
            "points": 42500,
        }

        if self.llm is not None and os.environ.get("ANTHROPIC_API_KEY"):
            with self.llm.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"Loyalty status for {account_id}",
                }],
            ) as stream:
                for chunk in stream.text_stream:
                    await event_queue.enqueue_event(         # ②
                        TaskArtifactUpdateEvent(
                            task_id=task_id,
                            context_id=context_id,
                            artifact=Artifact(
                                artifact_id=f"loyalty-{account_id}",
                                parts=[Part(text=chunk)],
                            ),
                            append=True,
                        )
                    )

        await event_queue.enqueue_event(                     # ③
            TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                artifact=Artifact(
                    artifact_id=f"loyalty-{account_id}",
                    parts=[data_part(payload)],
                ),
                last_chunk=True,
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            )
        )
        return payload

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "offline",
                context_id=context.context_id or "offline",
                status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
            )
        )


def _account_id(context: RequestContext) -> str:
    message = getattr(context, "message", None)
    parts = getattr(message, "parts", []) or []
    for part in parts:
        which = getattr(part, "WhichOneof", None)
        if callable(which) and which("content") == "data":
            fields = part.data.struct_value.fields
            if "accountId" in fields:
                return fields["accountId"].string_value
    return "offline"


def build_card() -> AgentCard:
    return AgentCard(
        name="HotelLoyaltyAgent",
        description="Hotel loyalty status and redemption lookup.",
        version="1.2.0",
        supported_interfaces=[
            AgentInterface(
                url="https://loyalty.hotelpartner.com/a2a",
                protocol_binding="JSONRPC",
                protocol_version="1.0.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[AgentSkill(
            id="hotel-loyalty-lookup",
            name="Hotel Loyalty Lookup",
            description="Returns points balance and tier for a guest account.",
            tags=["loyalty", "hotel"],
        )],
    )


class _MemoryQueue:
    def __init__(self) -> None:
        self.events: list = []

    async def enqueue_event(self, event) -> None:
        self.events.append(event)


def main() -> int:
    import asyncio

    card = build_card()

    class _Ctx:
        message = None
        task_id = "offline"
        context_id = "offline"

    artifact = asyncio.run(
        HotelLoyaltyExecutor().execute(_Ctx(), _MemoryQueue())
    )
    print(json.dumps({
        "name": card.name,
        "url": card.supported_interfaces[0].url,
        "artifact": artifact,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
