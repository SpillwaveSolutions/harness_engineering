"""Tests for listing 11-06-interrupt-config.

The listing is a configuration literal — a dict mapping tool names to
either an interrupt spec (dict with allowed_decisions) or a boolean
disable flag. Load-bearing claims from §11.6:

1. `interrupt_config` exists at module scope.
2. `book_flight` (irreversible) is configured with full decision
   control: approve, edit, reject.
3. `search_flights` (reversible read-only) is configured False — no
   interrupt fires.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def cfg(load_listing):
    return load_listing("11-06-interrupt-config")


def test_interrupt_config_exists(cfg):
    assert hasattr(cfg, "interrupt_config")
    assert isinstance(cfg.interrupt_config, dict)


def test_book_flight_has_full_decision_control(cfg):
    book_flight = cfg.interrupt_config["book_flight"]
    assert isinstance(book_flight, dict)
    assert "allowed_decisions" in book_flight
    allowed = book_flight["allowed_decisions"]
    for decision in ("approve", "edit", "reject"):
        assert decision in allowed, (
            f"expected {decision!r} in book_flight allowed_decisions"
        )


def test_search_flights_is_not_interrupted(cfg):
    assert cfg.interrupt_config["search_flights"] is False


def test_irreversible_tool_is_dict_reversible_is_false(cfg):
    """The configuration encodes the §11.6 policy directly: dict for
    interrupted (irreversible) tools, False for non-interrupted
    (reversible) ones."""
    book_flight = cfg.interrupt_config["book_flight"]
    search_flights = cfg.interrupt_config["search_flights"]
    assert isinstance(book_flight, dict)
    assert search_flights is False
