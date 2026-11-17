"""Smoke test for the §1.8 skeleton — confirms it imports and the agent runs
with a stub model client, plus that a failing client surfaces the exception
(the starting point for Chapter 15's recovery patterns).
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass
class StubModelClient:
    fixed_response: str = "I have booked your trip to Paris."

    def complete(self, message: str) -> str:
        return self.fixed_response


class FailingModelClient:
    def complete(self, message: str) -> str:
        raise RuntimeError("model down")


def test_skeleton_returns_stub_response(load_listing):
    listing = load_listing("01-02-travel-agent-skeleton")
    agent = listing.TravelBookingAgent(model_client=StubModelClient())
    assert agent.run("Rebook this customer") == "I have booked your trip to Paris."


def test_skeleton_propagates_client_exception(load_listing):
    listing = load_listing("01-02-travel-agent-skeleton")
    agent = listing.TravelBookingAgent(model_client=FailingModelClient())
    with pytest.raises(RuntimeError, match="model down"):
        agent.run("Rebook this customer")
