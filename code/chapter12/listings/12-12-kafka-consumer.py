import json
import os
import sys

from a2a.client import Client
from a2a.types import Message, Part, Role, SendMessageRequest
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from google.protobuf.struct_pb2 import Struct, Value

BOOKING_REQUESTS_TOPIC = "hotel-loyalty-requests"
RESULTS_TOPIC = "hotel-loyalty-results"


def data_part(payload: dict) -> Part:
    struct = Struct()
    struct.update(payload)
    return Part(data=Value(struct_value=struct))


async def run_loyalty_consumer(bootstrap_servers: str, a2a_client: Client):
    sample = {"accountId": "offline", "requestType": "full_status"}
    message = Message(
        message_id="offline-loyalty",
        role=Role.ROLE_USER,
        parts=[data_part(sample)],
    )
    if os.environ.get("HARNESS_LIVE_API") != "1":
        print(
            "Kafka consumer is offline; no broker connection was opened.",
            file=sys.stderr,
        )
        return [{
            "topic": BOOKING_REQUESTS_TOPIC,
            "results_topic": RESULTS_TOPIC,
            "bootstrap_servers": bootstrap_servers,
            "status": "offline",
            "parts": len(message.parts),
        }]

    if not hasattr(a2a_client, "send_message"):
        print(
            "HARNESS_LIVE_API=1 but no A2A client was provided. "
            "Not connecting to Kafka.",
            file=sys.stderr,
        )
        return [{
            "status": "skipped",
            "reason": "missing A2A client",
        }]
    try:
        return await _consume_live(
            bootstrap_servers, a2a_client, data_part, Message, Role
        )
    except (
        OSError, RuntimeError, ConnectionError, TimeoutError, KafkaError
    ) as exc:
        print(
            "Live Kafka/A2A call failed "
            f"({exc.__class__.__name__}: {exc}). Not retrying.",
            file=sys.stderr,
        )
        return [{"status": "error", "reason": str(exc)}]


async def _consume_live(
    bootstrap_servers, a2a_client, data_part, message_cls, role
):
    consumer = AIOKafkaConsumer(
        BOOKING_REQUESTS_TOPIC,
        bootstrap_servers=bootstrap_servers,
        group_id="hotel-loyalty-consumers",
        key_deserializer=lambda k: k.decode(),  # contextId as partition key
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    collected: list[dict] = []
    await consumer.start()
    try:
        async for record in consumer:
            context_id = record.key              # ① A2A contextId = Kafka partition key
            payload = record.value
            live_message = message_cls(
                message_id=str(context_id),
                role=role.ROLE_USER,
                parts=[data_part(payload)],
            )
            request = SendMessageRequest(message=live_message)
            async for event in a2a_client.send_message(request):
                collected.append({
                    "context_id": context_id,
                    "task_id": getattr(event, "task_id", None),
                    "state": str(
                        getattr(getattr(event, "status", None), "state", "")
                    ),
                })
    finally:
        await consumer.stop()
    return collected


def main() -> int:
    import asyncio

    result = asyncio.run(run_loyalty_consumer("localhost:9092", object()))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
