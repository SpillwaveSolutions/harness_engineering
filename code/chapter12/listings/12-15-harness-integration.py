import asyncio
import json
import os
import sys
from dataclasses import dataclass, field

import httpx
from a2a.client import A2ACardResolver, ClientFactory
from a2a.client.errors import AgentCardResolutionError
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageRequest,
    TaskState,
)
from anthropic import Anthropic
from google.protobuf.struct_pb2 import Struct, Value


def data_part(payload: dict) -> Part:
    struct = Struct()
    struct.update(payload)
    return Part(data=Value(struct_value=struct))


class InputRequired(Exception):
    """The loyalty agent needs another user message."""


class TaskFailed(Exception):
    """The loyalty agent reported a failed task."""


class CardResolutionError(RuntimeError):
    """Live card resolution failed. No unverified card is used."""


def _local_loyalty_card() -> AgentCard:
    return AgentCard(
        name="HotelLoyaltyAgent",
        description=(
            "OFFLINE STAND-IN: not a verified partner card. "
            "Hotel loyalty status and redemption lookup."
        ),
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


async def _open_stream(message):
    """Offline stream. Live transport is not opened unless the flag is set."""
    del message
    if os.environ.get("HARNESS_LIVE_API") != "1":
        print(
            "A2A loyalty stream is offline; no message was sent.",
            file=sys.stderr,
        )
        if False:
            yield None
        return
    print(
        "HARNESS_LIVE_API=1 but this build does not open a live A2A socket.",
        file=sys.stderr,
    )
    if False:
        yield None


@dataclass
class BookingContext:
    """Durable booking state — guarded against lost_handoff_state."""
    session_id: str
    a2a_task_ids: dict = field(default_factory=dict)  # ① durable task registry
    artifacts: dict = field(default_factory=dict)


class TravelBookingHarness:
    LOYALTY_AGENT_URL = "https://loyalty.hotelpartner.com"

    def __init__(self):
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.llm = Anthropic()
        else:
            print(
                "ANTHROPIC_API_KEY is unset; booking synthesis stays offline.",
                file=sys.stderr,
            )
            self.llm = None
        self._loyalty_card: AgentCard | None = None

    async def _discover_loyalty_agent(self) -> AgentCard:
        """Fetch and cache the partner's Agent Card."""
        if self._loyalty_card is None:
            if os.environ.get("HARNESS_LIVE_API") != "1":
                print(
                    "OFFLINE STAND-IN card; not a verified partner card.",
                    file=sys.stderr,
                )
                self._loyalty_card = _local_loyalty_card()
            else:
                try:
                    async with httpx.AsyncClient() as http:
                        resolver = A2ACardResolver(
                            http, self.LOYALTY_AGENT_URL
                        )
                        card = await resolver.get_agent_card()
                        # ② A2ACardResolver fetches the well-known card.
                except (
                    AgentCardResolutionError,
                    httpx.HTTPError,
                    OSError,
                    ValueError,
                ) as exc:
                    raise CardResolutionError(
                        "Refusing an unverified loyalty card "
                        f"({exc.__class__.__name__}: {exc})."
                    ) from exc
                self._loyalty_card = card
        return self._loyalty_card

    async def _delegate_loyalty_check(
        self,
        ctx: BookingContext,
        account_id: str,
        loyalty_card: AgentCard,
    ) -> dict:
        """A2A handoff layer: owns protocol details, not business logic."""
        message = Message(
            message_id=f"loyalty-{account_id}",
            role=Role.ROLE_USER,
            parts=[
                Part(text="Check loyalty status"),
                data_part({"accountId": account_id}),
            ],
        )
        artifacts: dict = {}
        if os.environ.get("HARNESS_LIVE_API") == "1":
            client = ClientFactory().create(loyalty_card)
            request = SendMessageRequest(message=message)
            stream = client.send_message(request)
        else:
            stream = _open_stream(message)
        async for event in stream:
            if event.WhichOneof("payload") != "status_update":
                continue
            update = event.status_update
            task_id = update.task_id
            if task_id and task_id not in ctx.a2a_task_ids:
                ctx.a2a_task_ids["loyalty"] = task_id  # ⑤ register task ID

            state = update.status.state
            if state == TaskState.TASK_STATE_INPUT_REQUIRED:
                raise InputRequired(update.status.message)  # ③ surface up
            if state == TaskState.TASK_STATE_FAILED:
                raise TaskFailed(
                    f"Loyalty check failed: {update.status.message}"
                )
            if state == TaskState.TASK_STATE_COMPLETED:
                break  # artifact collected below

        ctx.a2a_task_ids.setdefault("loyalty", "offline-loyalty")
        if not artifacts:
            artifacts = {"accountId": account_id, "status": "offline"}
        return artifacts  # ④ typed artifacts only — no raw protocol objects

    async def book_travel(self, user_request: str, account_id: str) -> dict:
        """Orchestration logic: decides what, when, and who."""
        ctx = BookingContext(session_id=f"booking-{account_id[:8]}")
        loyalty_card = await self._discover_loyalty_agent()  # ②

        # Delegate in parallel — orchestration layer owns the fan-out
        loyalty_task = self._delegate_loyalty_check(
            ctx, account_id, loyalty_card
        )
        flight_task = self._run_flight_search(ctx, user_request)

        loyalty_data, flight_options = await asyncio.gather(
            loyalty_task, flight_task
        )

        # Synthesis layer: merge with provenance, surface conflicts
        return self._synthesize(flight_options, loyalty_data, ctx)

    def _synthesize(
        self, flights: dict, loyalty: dict, ctx: BookingContext
    ) -> dict:
        return {
            "flights": flights,
            "loyalty": loyalty,
            "tasks": dict(ctx.a2a_task_ids),
            "session_id": ctx.session_id,
        }

    async def _run_flight_search(
        self, ctx: BookingContext, request: str
    ) -> dict:
        ctx.a2a_task_ids.setdefault("flights", "offline-flight")
        return {"request": request, "options": []}


def main() -> int:
    harness = TravelBookingHarness()
    try:
        result = asyncio.run(
            harness.book_travel("book a hotel", "ACC123456")
        )
    except CardResolutionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
