"""Tests for listing 15-05-replay-debugger (§15.5).

Verifies:
  - Module imports without NameError (HarnessCheckpoint, ReplayExecutor resolved).
  - _get_live_fingerprint() is callable and returns a string.
  - replay_debug returns correct structure when all tool calls replay cleanly.
  - replay_debug sets model_pin_warning=True when fingerprint differs.
  - replay_debug reports fidelity=1.0 when every step replays from fixtures.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-05-replay-debugger.py"
    # Clear cached sub-modules so we get a fresh load each test run
    for key in list(sys.modules.keys()):
        if key.startswith("listing_15_0"):
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location("listing_15_05", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_05"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _write_checkpoint(tmp_path: Path, fingerprint: str = "fp-abc123") -> None:
    """Write a minimal checkpoint JSON that replay_debug can load."""
    import importlib.util as ilu
    import sys as _sys

    cp_path = LISTINGS_DIR / "15-02-checkpoint-writer.py"
    spec = ilu.spec_from_file_location("listing_15_02_helper", cp_path)
    cp_mod = ilu.module_from_spec(spec)
    _sys.modules["listing_15_02_helper"] = cp_mod
    spec.loader.exec_module(cp_mod)  # type: ignore[union-attr]

    args = {"origin": "JFK", "dest": "LHR", "date": "2026-06-01"}
    key = f"search_flights:{json.dumps(args, sort_keys=True)}"

    cp = cp_mod.HarnessCheckpoint(
        session_id="sess1",
        step="step1",
        tool_results={key: {"flights": ["AA1"]}},
        model_version="claude-sonnet-4-6",
        system_fingerprint=fingerprint,
        cost_tokens_in=100,
        cost_tokens_out=50,
        cost_usd=0.002,
        git_sha="deadbeef",
        transcript_hash="hash-xyz",
    )
    cp.write(tmp_path)


def test_module_imports_no_nameerror():
    """§15.5: listing imports without NameError (HarnessCheckpoint, ReplayExecutor defined)."""
    mod = _load_module()
    assert hasattr(mod, "HarnessCheckpoint"), "HarnessCheckpoint must be imported"
    assert hasattr(mod, "ReplayExecutor"), "ReplayExecutor must be imported"
    assert hasattr(mod, "replay_debug"), "replay_debug must be defined"


def test_get_live_fingerprint_returns_string():
    """§15.5: _get_live_fingerprint() is callable and returns a str."""
    mod = _load_module()
    result = mod._get_live_fingerprint()
    assert isinstance(result, str)
    assert len(result) > 0


def test_replay_debug_returns_expected_keys(tmp_path):
    """§15.5: replay_debug returns fidelity, steps_replayed, model_pin_warning."""
    _write_checkpoint(tmp_path)
    mod = _load_module()
    result = mod.replay_debug("sess1", "step1", tmp_path)
    assert "fidelity" in result
    assert "steps_replayed" in result
    assert "model_pin_warning" in result


def test_replay_debug_full_fidelity(tmp_path):
    """§15.5: fidelity==1.0 when every recorded tool step replays cleanly."""
    _write_checkpoint(tmp_path)
    mod = _load_module()
    result = mod.replay_debug("sess1", "step1", tmp_path)
    assert result["fidelity"] == 1.0
    assert result["steps_replayed"] == 1


def test_replay_debug_model_pin_warning_when_mismatch(tmp_path):
    """§15.5: model_pin_warning==True when fingerprint differs from live."""
    # checkpoint uses a specific fingerprint; live returns a sentinel
    _write_checkpoint(tmp_path, fingerprint="fp-old")
    mod = _load_module()
    result = mod.replay_debug("sess1", "step1", tmp_path)
    # The live fingerprint is the sentinel string, not "fp-old"
    assert result["model_pin_warning"] is True


def test_replay_debug_no_pin_warning_when_fingerprint_matches(tmp_path):
    """§15.5: model_pin_warning==False when fingerprint matches live sentinel."""
    sentinel = "live-fingerprint-unavailable-in-replay-mode"
    _write_checkpoint(tmp_path, fingerprint=sentinel)
    mod = _load_module()
    result = mod.replay_debug("sess1", "step1", tmp_path)
    assert result["model_pin_warning"] is False
