"""Tests for listing 12-12-kafka-consumer.

Depends on aiokafka and a2a-sdk. Skips gracefully if either is not
installed.

Structural claims from §12.12:
- The listing exports an async function `run_loyalty_consumer` that
  bridges a Kafka topic to an A2A client.
- Module-level constants: BOOKING_REQUESTS_TOPIC and RESULTS_TOPIC
  define the Kafka topic names used by the consumer.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-12-kafka-consumer")
    assert module is not None


def test_run_loyalty_consumer_is_callable(load_listing):
    module = load_listing("12-12-kafka-consumer")
    assert callable(module.run_loyalty_consumer)


def test_topic_constants_defined(load_listing):
    module = load_listing("12-12-kafka-consumer")
    assert hasattr(module, "BOOKING_REQUESTS_TOPIC")
    assert hasattr(module, "RESULTS_TOPIC")


async def test_consumer_stays_offline(load_listing, monkeypatch):
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    module = load_listing("12-12-kafka-consumer")
    result = await module.run_loyalty_consumer("localhost:9092", object())
    assert result[0]["status"] == "offline"
    assert result[0]["topic"] == "hotel-loyalty-requests"
    assert result[0]["parts"] == 1
