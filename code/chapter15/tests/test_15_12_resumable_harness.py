"""Tests for listing 15-12-resumable-harness (§15.12).

Verifies:
  - load_plan returns None when feature_list.json is absent.
  - load_plan returns a list of dicts when feature_list.json is present.
  - run() dispatches to _run_initializer when no plan exists (no feature_list.json).
  - run() dispatches to _run_coding_session when a plan is present.
  - _run_coding_session returns all_features_pass when no incomplete features remain.

Uses tempfile.TemporaryDirectory + git init so the listing's git commit calls succeed.
anthropic.Anthropic is mocked to avoid live API calls.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-12-resumable-harness.py"
    spec = importlib.util.spec_from_file_location("listing_15_12", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_12"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _init_git_repo(project_dir: Path) -> None:
    """Initialize a bare git repo so the listing's git commit calls succeed."""
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir, check=True, capture_output=True,
    )
    (project_dir / ".gitkeep").write_text("")
    subprocess.run(["git", "add", ".gitkeep"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=project_dir, check=True, capture_output=True,
    )


def _make_harness(mod, project_dir: Path, session_id: str = "sess-test"):
    """Instantiate ResumableStateHarness with a mocked anthropic client."""
    with patch("anthropic.Anthropic"):
        harness = mod.ResumableStateHarness(project_dir, session_id)
    return harness


ALL_PASSES_FEATURES = [
    {
        "category": "flight",
        "description": "Search flights",
        "steps": ["Call search_flights"],
        "passes": True,
    },
    {
        "category": "hotel",
        "description": "Book hotel",
        "steps": ["Call book_hotel"],
        "passes": True,
    },
]

MIXED_FEATURES = [
    {
        "category": "flight",
        "description": "Search flights",
        "steps": ["Call search_flights"],
        "passes": True,
    },
    {
        "category": "hotel",
        "description": "Book hotel",
        "steps": ["Call book_hotel"],
        "passes": False,
    },
]


def test_module_imports():
    """§15.12: listing imports without error; ResumableStateHarness defined."""
    mod = _load_module()
    assert hasattr(mod, "ResumableStateHarness")


def test_load_plan_returns_none_when_absent():
    """§15.12 branch ①: load_plan returns None when feature_list.json does not exist."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        harness = _make_harness(mod, project_dir)
        result = harness.load_plan()
    assert result is None


def test_load_plan_returns_list_when_present():
    """§15.12 branch ①: load_plan returns a list of dicts when feature_list.json is present."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        (project_dir / "feature_list.json").write_text(
            json.dumps(MIXED_FEATURES, indent=2)
        )
        harness = _make_harness(mod, project_dir)
        result = harness.load_plan()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["description"] == "Search flights"


def test_run_dispatches_to_initializer_when_no_plan():
    """§15.12 branch ②: run() calls _run_initializer when no feature_list.json exists."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        harness = _make_harness(mod, project_dir)
        result = harness.run()

        assert result.get("role") == "initializer"
        assert result.get("status") == "complete"
        assert (project_dir / "feature_list.json").exists()
        assert (project_dir / "claude-progress.txt").exists()


def test_run_dispatches_to_coding_session_when_plan_present():
    """§15.12 branch ④: run() calls _run_coding_session when feature_list.json is present."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        (project_dir / "feature_list.json").write_text(
            json.dumps(MIXED_FEATURES, indent=2)
        )
        harness = _make_harness(mod, project_dir)
        # patch the internal messages.create to avoid live calls during coding dispatch
        harness.client = MagicMock()
        harness.client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
        result = harness.run()

    assert result.get("role") == "coding_agent"


def test_run_returns_all_features_pass_when_no_incomplete():
    """§15.12 branch ④: _run_coding_session returns all_features_pass when plan is complete."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        (project_dir / "feature_list.json").write_text(
            json.dumps(ALL_PASSES_FEATURES, indent=2)
        )
        harness = _make_harness(mod, project_dir)
        result = harness.run()

    assert result.get("role") == "coding_agent"
    assert result.get("status") == "all_features_pass"
