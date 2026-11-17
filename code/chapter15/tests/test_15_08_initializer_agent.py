"""Tests for listing 15-08-initializer-agent (§15.8).

Verifies:
  - run_initializer raises FileExistsError when feature_list.json already exists.
  - run_initializer writes feature_list.json with all passes=False (Default-FAIL).
  - run_initializer writes claude-progress.txt with the four-section structure.
  - The returned Path points to the newly created feature_list.json.

Uses tempfile.TemporaryDirectory + git init so the listing's git commit succeeds.
anthropic.Anthropic().messages.create is mocked to avoid live API calls.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-08-initializer-agent.py"
    spec = importlib.util.spec_from_file_location("listing_15_08", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_08"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _init_git_repo(project_dir: Path) -> None:
    """Initialize a bare git repo and stage an initial file so commits succeed."""
    subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project_dir, check=True, capture_output=True,
    )
    # create an initial commit so the repo has a HEAD
    (project_dir / ".gitkeep").write_text("")
    subprocess.run(["git", "add", ".gitkeep"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=project_dir, check=True, capture_output=True,
    )


def _make_mock_response(features: list[dict]) -> MagicMock:
    """Build a mock anthropic response whose content[0].text is the JSON of features."""
    msg = MagicMock()
    msg.content = [MagicMock()]
    msg.content[0].text = json.dumps(features)
    return msg


SAMPLE_FEATURES = [
    {
        "category": "flight",
        "description": "Search flights by route and date",
        "steps": ["Call search_flights"],
        "passes": False,
    },
    {
        "category": "flight",
        "description": "Book selected flight",
        "steps": ["Call book_flight"],
        "passes": False,
    },
    {
        "category": "hotel",
        "description": "Book hotel linked to flight",
        "steps": ["Call book_hotel"],
        "passes": False,
    },
]


def test_module_imports():
    """§15.8: listing imports without error; run_initializer defined."""
    mod = _load_module()
    assert hasattr(mod, "run_initializer")


def test_raises_file_exists_when_already_initialized():
    """§15.8 branch ①: run_initializer raises FileExistsError when feature_list.json exists."""
    mod = _load_module()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        # Pre-create the plan file to simulate an already-initialized project
        (project_dir / "feature_list.json").write_text("[]")
        with pytest.raises(FileExistsError, match="Initializer has already run"):
            mod.run_initializer(project_dir)


def test_writes_feature_list_json_with_all_passes_false():
    """§15.8 branch ②/③: feature_list.json written with all passes=false (Default-FAIL)."""
    mod = _load_module()
    mock_response = _make_mock_response(SAMPLE_FEATURES)
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        with patch("anthropic.Anthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create.return_value = mock_response
            result_path = mod.run_initializer(project_dir)

        plan_path = project_dir / "feature_list.json"
        assert plan_path.exists(), "feature_list.json must be created"
        assert result_path == plan_path, "run_initializer must return the plan path"
        features = json.loads(plan_path.read_text())
        assert len(features) > 0, "feature list must not be empty"
        for feature in features:
            assert feature["passes"] is False, (
                f"Default-FAIL contract violated: feature '{feature.get('description')}' "
                f"has passes={feature['passes']!r}"
            )


def test_writes_claude_progress_txt_four_section_structure():
    """§15.8 branch ④: claude-progress.txt has Done/In Progress/Next/Notes sections."""
    mod = _load_module()
    mock_response = _make_mock_response(SAMPLE_FEATURES)
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        with patch("anthropic.Anthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create.return_value = mock_response
            mod.run_initializer(project_dir)

        progress_path = project_dir / "claude-progress.txt"
        assert progress_path.exists(), "claude-progress.txt must be created"
        content = progress_path.read_text()
        for section in ("## Done", "## In Progress", "## Next", "## Notes"):
            assert section in content, (
                f"claude-progress.txt missing required section '{section}'"
            )


def test_returns_plan_path():
    """§15.8: run_initializer returns the Path to feature_list.json."""
    mod = _load_module()
    mock_response = _make_mock_response(SAMPLE_FEATURES)
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        _init_git_repo(project_dir)
        with patch("anthropic.Anthropic") as mock_client_cls:
            mock_client_cls.return_value.messages.create.return_value = mock_response
            result = mod.run_initializer(project_dir)

        assert isinstance(result, Path)
        assert result.name == "feature_list.json"
