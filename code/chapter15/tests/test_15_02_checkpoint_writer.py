"""Tests for listing 15-02-checkpoint-writer (§15.2).

Verifies:
  - HarnessCheckpoint dataclass round-trips through write/load.
  - write() creates a file at the expected path.
  - load() reconstructs an identical object.
  - exists() returns True when the file is present, False when absent.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-02-checkpoint-writer.py"
    spec = importlib.util.spec_from_file_location("listing_15_02", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_02"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _make_checkpoint(mod, session_id: str = "s1", step: str = "step1"):
    return mod.HarnessCheckpoint(
        session_id=session_id,
        step=step,
        tool_results={},
        model_version="claude-sonnet-4-6",
        system_fingerprint="fp-abc123",
        cost_tokens_in=100,
        cost_tokens_out=50,
        cost_usd=0.002,
        git_sha="deadbeef",
        transcript_hash="hash-xyz",
    )


def test_module_imports():
    """§15.2: listing imports without error."""
    mod = _load_module()
    assert hasattr(mod, "HarnessCheckpoint")


def test_checkpoint_write_creates_file(tmp_path):
    """§15.2: write() creates a JSON file at session_id_step.json."""
    mod = _load_module()
    cp = _make_checkpoint(mod)
    out = cp.write(tmp_path)
    assert out.exists(), "write() must create the file"
    assert out.name == "s1_step1.json"


def test_checkpoint_round_trip(tmp_path):
    """§15.2: load(write()) reconstructs an identical HarnessCheckpoint."""
    mod = _load_module()
    cp = _make_checkpoint(mod)
    path = cp.write(tmp_path)
    loaded = mod.HarnessCheckpoint.load(path)
    assert loaded.session_id == cp.session_id
    assert loaded.step == cp.step
    assert loaded.model_version == cp.model_version
    assert loaded.system_fingerprint == cp.system_fingerprint
    assert loaded.transcript_hash == cp.transcript_hash
    assert loaded.git_sha == cp.git_sha


def test_checkpoint_stores_tool_results(tmp_path):
    """§15.2: tool_results dict is preserved through write/load."""
    mod = _load_module()
    cp = _make_checkpoint(mod)
    cp.tool_results = {
        'search_flights:{"dest":"LHR","origin":"JFK"}': {"flights": ["AA1"]}
    }
    path = cp.write(tmp_path)
    loaded = mod.HarnessCheckpoint.load(path)
    assert loaded.tool_results == cp.tool_results


def test_checkpoint_exists_true(tmp_path):
    """§15.2: exists() returns True after a write."""
    mod = _load_module()
    cp = _make_checkpoint(mod)
    cp.write(tmp_path)
    assert mod.HarnessCheckpoint.exists(tmp_path, "s1", "step1") is True


def test_checkpoint_exists_false(tmp_path):
    """§15.2: exists() returns False when no file is present."""
    mod = _load_module()
    assert mod.HarnessCheckpoint.exists(tmp_path, "missing", "step") is False
