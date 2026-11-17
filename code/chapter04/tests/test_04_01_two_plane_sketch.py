"""Structural tests for listing 04-01 (two-plane sketch).

The listing is a representative sketch: method bodies are Ellipsis by
design. These tests pin the structural contract the prose teaches —
the one-way dependency (control plane holds the data plane, never the
reverse) and the policy/execution method split.
"""
import importlib.util
from pathlib import Path

LISTING = Path(__file__).parent.parent / "listings" / "04-01-two-plane-sketch.py"


def _load():
    spec = importlib.util.spec_from_file_location("two_plane_sketch", LISTING)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_listing_imports_cleanly():
    mod = _load()
    assert hasattr(mod, "DataPlane")
    assert hasattr(mod, "ControlPlane")


def test_data_plane_exposes_pure_execution_methods():
    mod = _load()
    for method in ("call_model", "invoke_tool", "write_memory"):
        assert callable(getattr(mod.DataPlane, method))


def test_control_plane_holds_data_plane_reference():
    mod = _load()
    dp = mod.DataPlane()
    cp = mod.ControlPlane(dp)
    assert cp.dp is dp
    # The dependency points one way: DataPlane knows nothing of ControlPlane.
    assert not hasattr(dp, "cp")


def test_run_returns_offline_reply_for_the_goal():
    mod = _load()
    result = mod.ControlPlane(mod.DataPlane()).run("Book a flight to Tokyo.")
    assert result == "offline reply: Book a flight to Tokyo."


def test_run_escalates_when_the_turn_limit_is_already_spent():
    mod = _load()
    plane = mod.ControlPlane(mod.DataPlane())
    plane.turns = 1
    assert plane.run("anywhere") == "escalated"


def test_data_plane_tool_and_memory_return_concrete_values():
    mod = _load()
    plane = mod.DataPlane()
    assert plane.invoke_tool("search_flights", {"origin": "SFO"}) == (
        "invoked search_flights {'origin': 'SFO'}"
    )
    assert plane.write_memory("city", "Lisbon") == "Lisbon"
    assert plane.memory["city"] == "Lisbon"
    response = plane.call_model(
        [{"role": "user", "content": "hello"}],
        [],
    )
    assert response.stop_reason == "end_turn"
    assert response.content == "offline reply: hello"
