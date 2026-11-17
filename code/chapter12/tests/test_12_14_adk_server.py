"""Tests for listing 12-14-adk-server.

Depends on google.adk and a2a-sdk. Skips gracefully if either is not
installed.

Structural claims from §12.14 (ADK path):
- The listing exports a function `create_adk_a2a_server` that accepts
  an agent_card and returns an A2AStarletteApplication wrapping a
  Google ADK LlmAgent.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-14-adk-server")
    assert module is not None


def test_create_adk_a2a_server_is_callable(load_listing):
    module = load_listing("12-14-adk-server")
    assert callable(module.create_adk_a2a_server)


def test_create_adk_a2a_server_builds_fastapi_offline(load_listing):
    from a2a.types import (
        AgentCapabilities,
        AgentCard,
        AgentInterface,
        AgentSkill,
    )
    from fastapi import FastAPI

    module = load_listing("12-14-adk-server")
    card = AgentCard(
        name="HotelLoyaltyAgent",
        description="Hotel loyalty status and redemption lookup.",
        version="1.2.0",
        supported_interfaces=[
            AgentInterface(
                url="https://loyalty.example.test/a2a",
                protocol_binding="JSONRPC",
                protocol_version="1.0.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="hotel-loyalty-lookup",
                name="Hotel Loyalty Lookup",
                description="Points and tier.",
                tags=["loyalty"],
            )
        ],
    )
    app = module.create_adk_a2a_server(card)
    assert isinstance(app, FastAPI)
    assert len(app.routes) >= 1
