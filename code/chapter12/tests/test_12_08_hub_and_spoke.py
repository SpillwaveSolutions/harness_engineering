"""Tests for listing 12-08-hub-and-spoke.

Depends on a2a-sdk (A2AClient) and anthropic. Skips gracefully if either
is not installed.

Structural claims from §12.8:
- The listing exports a dataclass `SpokeResult` with fields: spoke_name,
  artifacts, task_id.
- The listing exports a class `TravelCoordinator` whose constructor
  accepts flight_client and loyalty_client (A2AClient instances), and
  which exposes an async `handle_request` method.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-08-hub-and-spoke")
    assert module is not None


def test_travel_coordinator_class_exists(load_listing):
    module = load_listing("12-08-hub-and-spoke")
    assert hasattr(module, "TravelCoordinator")


def test_spoke_result_class_exists(load_listing):
    module = load_listing("12-08-hub-and-spoke")
    assert hasattr(module, "SpokeResult")


async def test_handle_request_merges_offline_spokes(load_listing):
    module = load_listing("12-08-hub-and-spoke")
    coordinator = module.TravelCoordinator(
        flight_client=object(),
        loyalty_client=object(),
    )
    result = await coordinator.handle_request("SFO next week", "ACC123")
    assert result["status"] == "ok"
    names = [spoke["name"] for spoke in result["spokes"]]
    assert names == ["flight-search", "hotel-loyalty"]
