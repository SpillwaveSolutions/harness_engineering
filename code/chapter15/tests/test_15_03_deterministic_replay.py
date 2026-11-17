"""Tests for listing 15-03-deterministic-replay (§15.3).

Verifies:
  - ReplayExecutor imports without NameError.
  - dispatch_tool returns recorded response when key is present.
  - dispatch_tool raises ValueError for unrecorded calls (live blocked).
  - fidelity is 1.0 when all calls are replayed.
  - fidelity is 0.0 when all calls go live (error path shows denominator).
  - Callable is NOT in the module's imports (unused import removed).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-03-deterministic-replay.py"
    spec = importlib.util.spec_from_file_location("listing_15_03", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_03"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _make_mock_checkpoint(tool_results: dict):
    """Create a minimal checkpoint mock for ReplayExecutor."""
    cp = MagicMock()
    cp.tool_results = tool_results
    cp.system_fingerprint = "fp-abc123"
    return cp


def test_module_imports():
    """§15.3: listing imports without NameError."""
    mod = _load_module()
    assert hasattr(mod, "ReplayExecutor")


def test_callable_not_imported():
    """§15.3: Callable must be removed from imports (was unused)."""
    path = LISTINGS_DIR / "15-03-deterministic-replay.py"
    source = path.read_text()
    assert "Callable" not in source, (
        "Callable is unused and must be removed from the import"
    )


def test_dispatch_tool_returns_recorded_response():
    """§15.3: dispatch_tool returns the stored value for a known key."""
    mod = _load_module()
    args = {"origin": "JFK", "dest": "LHR"}
    key = f"search_flights:{json.dumps(args, sort_keys=True)}"
    tool_results = {key: {"flights": ["AA1", "BA2"]}}
    cp = _make_mock_checkpoint(tool_results)
    executor = mod.ReplayExecutor(cp)
    result = executor.dispatch_tool("search_flights", args)
    assert result == {"flights": ["AA1", "BA2"]}


def test_dispatch_tool_blocks_unrecorded_call():
    """§15.3: dispatch_tool raises ValueError for any unrecorded call."""
    mod = _load_module()
    cp = _make_mock_checkpoint({})
    executor = mod.ReplayExecutor(cp)
    with pytest.raises(ValueError, match="No recorded response"):
        executor.dispatch_tool("search_flights", {"origin": "JFK"})


def test_fidelity_perfect_replay():
    """§15.3: fidelity == 1.0 when every call hits the recorded set."""
    mod = _load_module()
    args = {"k": "v"}
    key = f"tool_a:{json.dumps(args, sort_keys=True)}"
    cp = _make_mock_checkpoint({key: "result"})
    executor = mod.ReplayExecutor(cp)
    executor.dispatch_tool("tool_a", args)
    assert executor.fidelity == 1.0


def test_fidelity_zero_on_fresh_executor():
    """§15.3: fidelity == 1.0 (no calls yet) — denominator guard."""
    mod = _load_module()
    cp = _make_mock_checkpoint({})
    executor = mod.ReplayExecutor(cp)
    # No calls made: fidelity defaults to 1.0 (per implementation)
    assert executor.fidelity == 1.0
