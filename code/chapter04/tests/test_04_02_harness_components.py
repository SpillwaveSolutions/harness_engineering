"""Structural tests for listing 04-02 (HarnessComponents checklist).

Pins the seven-field contract the chapter teaches: every production
harness has all seven, and validators/tools are separate fields.
"""
import dataclasses
import importlib.util
from pathlib import Path

LISTING = Path(__file__).parent.parent / "listings" / "04-02-harness-components.py"

SEVEN = [
    "context_manager",
    "memory",
    "validators",
    "tools",
    "observability",
    "recovery",
    "coordination",
]


def _load():
    spec = importlib.util.spec_from_file_location("harness_components", LISTING)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_listing_imports_cleanly():
    assert hasattr(_load(), "HarnessComponents")


def test_exactly_seven_components_in_canonical_order():
    mod = _load()
    fields = [f.name for f in dataclasses.fields(mod.HarnessComponents)]
    assert fields == SEVEN


def test_validators_and_tools_are_separate_fields():
    mod = _load()
    names = {f.name for f in dataclasses.fields(mod.HarnessComponents)}
    assert "validators" in names and "tools" in names


def test_components_hold_concrete_values():
    mod = _load()
    item = mod.HarnessComponents(
        context_manager="ctx",
        memory={"city": "Lisbon"},
        validators=[],
        tools={"search": lambda: "ok"},
        observability="spans",
        recovery="retry",
        coordination=None,
    )
    assert item.memory == {"city": "Lisbon"}
    assert item.coordination is None
    assert item.tools["search"]() == "ok"
    assert item.observability == "spans"
