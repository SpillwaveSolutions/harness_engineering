"""Tests for listing 12-14-a2a-sdk-server.

Depends on a2a-sdk (AgentExecutor, TaskContext, AgentCard, etc.) and
anthropic. Skips gracefully if either is not installed.

Structural claims from §12.14 (A2A SDK path):
- The listing exports a class `HotelLoyaltyExecutor` with async
  `execute` and `cancel` methods.
- The listing exports a function `build_card` that returns an AgentCard
  with the correct name and skill metadata.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-14-a2a-sdk-server")
    assert module is not None


def test_hotel_loyalty_executor_class_exists(load_listing):
    module = load_listing("12-14-a2a-sdk-server")
    assert hasattr(module, "HotelLoyaltyExecutor")


def test_build_card_is_callable(load_listing):
    module = load_listing("12-14-a2a-sdk-server")
    assert callable(module.build_card)


def test_build_card_names_the_loyalty_agent(load_listing):
    module = load_listing("12-14-a2a-sdk-server")
    card = module.build_card()
    assert card.name == "HotelLoyaltyAgent"
    assert card.skills[0].id == "hotel-loyalty-lookup"
    assert card.supported_interfaces[0].url.endswith("/a2a")


async def test_execute_returns_offline_artifact(load_listing, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("12-14-a2a-sdk-server")
    class _Ctx:
        message = None
        task_id = "offline"
        context_id = "offline"

    class _Queue:
        def __init__(self) -> None:
            self.events = []

        async def enqueue_event(self, event) -> None:
            self.events.append(event)

    artifact = await module.HotelLoyaltyExecutor().execute(
        _Ctx(), _Queue()
    )
    assert artifact["status"] == "platinum"
    assert artifact["accountId"] == "offline"
    assert "points" in artifact
