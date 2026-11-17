"""Tests for listing 15-09-coding-agent.

The offline path returns a status dict and does not call the model.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-09-coding-agent.py"
    spec = importlib.util.spec_from_file_location("listing_15_09", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_09"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_missing_plan_raises(tmp_path):
    mod = _load_module()
    try:
        mod.run_coding_session(tmp_path, 1)
    except FileNotFoundError as exc:
        assert "feature_list.json" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_complete_plan_returns_complete(tmp_path):
    mod = _load_module()
    plan = tmp_path / "feature_list.json"
    plan.write_text(json.dumps([
        {"description": "Search flights", "passes": True, "steps": []}
    ]))
    result = mod.run_coding_session(tmp_path, 2)
    assert result == {"status": "complete", "session": 2}


def test_offline_session_returns_status(tmp_path, monkeypatch):
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_module()
    (tmp_path / "feature_list.json").write_text(json.dumps([
        {
            "description": "Search flights",
            "passes": False,
            "steps": ["Call search_flights"],
        }
    ]))
    result = mod.run_coding_session(tmp_path, 3)
    assert result["status"] == "offline"
    assert result["session"] == 3
    assert result["feature"] == "Search flights"
