"""Tests for listing 03-12-orchestrator-workers (§3.12).

Validates the orchestrator-workers pipeline (the dynamic project manager):
- call_planner returns a list[str]
- call_worker returns a str
- call_compiler accepts list[str] and returns a str
- The compiled LangGraph flow runs an issue through plan → workers → synth.

"""

from __future__ import annotations


def test_call_planner_returns_list_of_strings(load_listing):
    """§3.12: call_planner must return list[str] for any issue string."""
    listing = load_listing("03-12-orchestrator-workers")

    tasks = listing.call_planner("authentication bug across multiple files")

    assert isinstance(tasks, list)
    assert len(tasks) >= 1
    assert all(isinstance(t, str) for t in tasks)


def test_call_worker_returns_string(load_listing):
    """§3.12: call_worker must return a str for any task string."""
    listing = load_listing("03-12-orchestrator-workers")

    output = listing.call_worker("investigate: auth module")

    assert isinstance(output, str)
    assert output  # non-empty


def test_call_compiler_returns_string(load_listing):
    """§3.12: call_compiler must return a str given a list of outputs."""
    listing = load_listing("03-12-orchestrator-workers")

    patch = listing.call_compiler(["fix auth.py", "fix session.py"])

    assert isinstance(patch, str)
    assert patch  # non-empty


def test_flow_runs_end_to_end(load_listing):
    """§3.12: the compiled flow must process an issue and produce a patch."""
    listing = load_listing("03-12-orchestrator-workers")

    result = listing.flow.invoke({"issue": "login fails after token expiry"})

    assert "patch" in result
    assert isinstance(result["patch"], str)
    assert result["patch"]


def test_flow_populates_intermediate_state(load_listing):
    """§3.12: tasks and outputs are populated after the flow completes."""
    listing = load_listing("03-12-orchestrator-workers")

    result = listing.flow.invoke({"issue": "null pointer in payment handler"})

    assert "tasks" in result
    assert isinstance(result["tasks"], list)
    assert "outputs" in result
    assert isinstance(result["outputs"], list)
    assert len(result["outputs"]) == len(result["tasks"])
