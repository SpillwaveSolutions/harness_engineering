"""Tests for listing 12-11-hybrid-agent.

Depends on fastapi, mcp (FastMCP), and a2a-sdk. Skips gracefully if any
of these are not installed.

Structural claims from §12.11:
- The listing exports a function `create_hybrid_server` that returns a
  FastAPI application mounting both an MCP surface and an A2A surface.
- The listing exports `build_a2a_app` and the `mcp` FastMCP instance.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-11-hybrid-agent")
    assert module is not None


def test_create_hybrid_server_is_callable(load_listing):
    module = load_listing("12-11-hybrid-agent")
    assert callable(module.create_hybrid_server)


def test_build_a2a_app_is_callable(load_listing):
    module = load_listing("12-11-hybrid-agent")
    assert callable(module.build_a2a_app)


def test_get_loyalty_balance_offline(load_listing):
    module = load_listing("12-11-hybrid-agent")
    balance = module.get_loyalty_balance("ACC123")
    assert balance["account_id"] == "ACC123"
    assert balance["status"] == "offline"
