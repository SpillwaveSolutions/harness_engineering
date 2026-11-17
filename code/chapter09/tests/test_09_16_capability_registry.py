"""Skill frontmatter loads, and dispatch enforces the caller allow-list."""

from __future__ import annotations

from pathlib import Path


def test_register_skill_reads_frontmatter(load_listing) -> None:
    module = load_listing("09-16-capability-registry")
    registry = module.CapabilityRegistry()
    skill = (
        Path(__file__).parent.parent / "listings" / "09-11-skill-md.txt"
    )
    registry.register_skill(str(skill))
    stored = registry._skills["flight-cancellation"]
    assert stored["name"] == "flight-cancellation"
    assert stored["description"].startswith("Guide")
    assert "cancel_booking" in stored["allowed_tools"]
    assert stored["context"] == "fork"


def test_dispatch_allows_named_caller(load_listing) -> None:
    module = load_listing("09-16-capability-registry")
    registry = module.CapabilityRegistry()

    def handler(origin: str) -> dict:
        return {"origin": origin}

    registry.register_tool(
        "search_flights",
        "search",
        {"type": "object"},
        handler,
        ["booking-agent"],
    )
    denied = registry.dispatch_tool(
        "search_flights", {"origin": "JFK"}, "s", "stranger"
    )
    assert denied == {"error": "Permission denied", "is_retryable": False}
    allowed = registry.dispatch_tool(
        "search_flights", {"origin": "JFK"}, "s", "booking-agent"
    )
    assert allowed == {"origin": "JFK"}
