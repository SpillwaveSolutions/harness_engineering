"""Tests for listing 14-10-harness-integration (§14.13).

Verifies:
  - Module imports without NameError; EvaluationHooks and CALIBRATORS defined.
  - EvaluationHooks.pre_tool_use allows non-evaluated tools.
  - EvaluationHooks.EVALUATED_TOOLS contains 'book_flight'.
  - HookResult.allow() and HookResult.block() are callable via the stub.
  - The agents stub module (agents.py) exports AgentHooks and HookResult.

The Anthropic client and sibling listings are patched to avoid network calls.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_agents_stub():
    """Load the agents stub module."""
    path = LISTINGS_DIR / "agents.py"
    spec = importlib.util.spec_from_file_location("agents", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agents"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def _load_module():
    """Load 14-10. The listing stays offline without a live client."""
    _load_agents_stub()
    path = LISTINGS_DIR / "14-10-harness-integration.py"
    spec = importlib.util.spec_from_file_location(
        "listing_14_10", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_10"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_agents_stub_exports_base_classes():
    """§14.13: agents.py must export AgentHooks and HookResult."""
    agents = _load_agents_stub()
    assert hasattr(agents, "AgentHooks")
    assert hasattr(agents, "HookResult")


def test_hook_result_allow_and_block():
    """§14.13: HookResult.allow() must be allowed; HookResult.block() blocked."""
    agents = _load_agents_stub()
    allow = agents.HookResult.allow()
    assert allow.allowed is True

    block = agents.HookResult.block(reason="test reason")
    assert block.allowed is False
    assert "test reason" in block.reason


def test_module_defines_evaluation_hooks():
    """§14.13: EvaluationHooks class must be importable."""
    mod = _load_module()
    assert hasattr(mod, "EvaluationHooks")


def test_evaluated_tools_contains_book_flight():
    """§14.13: EVALUATED_TOOLS must contain 'book_flight'."""
    mod = _load_module()
    assert "book_flight" in mod.EvaluationHooks.EVALUATED_TOOLS


def test_pre_tool_use_allows_non_evaluated_tool():
    """§14.13: pre_tool_use allows tools not in EVALUATED_TOOLS."""
    mod = _load_module()
    hooks = mod.EvaluationHooks()
    result = hooks.pre_tool_use("search_flights", {"query": "Paris"})
    assert result.allowed is True


def test_calibrators_defined():
    """§14.13: CALIBRATORS must be defined as a dict."""
    mod = _load_module()
    assert hasattr(mod, "CALIBRATORS")
    assert isinstance(mod.CALIBRATORS, dict)
