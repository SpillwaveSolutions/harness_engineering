"""Replay debugger — re-executes a checkpointed session up to a failing step.

Depends on HarnessCheckpoint (15-02) and ReplayExecutor (15-03).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Cross-listing loader
# ---------------------------------------------------------------------------
_LISTINGS = Path(__file__).parent


def _load_listing(slug: str):
    """Load a sibling listing by its NN-MM-slug name."""
    path = _LISTINGS / f"{slug}.py"
    mod_name = slug.replace("-", "_")
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_cp_mod = _load_listing("15-02-checkpoint-writer")
HarnessCheckpoint = _cp_mod.HarnessCheckpoint                     # ①

_re_mod = _load_listing("15-03-deterministic-replay")
ReplayExecutor = _re_mod.ReplayExecutor                           # ①


# ---------------------------------------------------------------------------
# Live fingerprint stub
# ---------------------------------------------------------------------------
def _get_live_fingerprint() -> str:                               # ②
    """Return a placeholder for the current backend fingerprint.

    In production, query the model metadata endpoint. In replay mode this
    sentinel lets the caller detect model-version drift without a live call.
    """
    return "live-fingerprint-unavailable-in-replay-mode"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def replay_debug(
    session_id: str,
    failing_step: str,
    checkpoint_dir: Path,
) -> dict:
    """Re-execute a session up to the failing step using recorded responses."""
    cp = HarnessCheckpoint.load(                                  # ③
        checkpoint_dir / f"{session_id}_{failing_step}.json"
    )
    executor = ReplayExecutor(cp)

    results = {}
    for step in cp.tool_results:               # ④
        # step key is "tool_name:json_args"; split once and parse args
        tool_name, args_json = step.split(":", 1)
        args = json.loads(args_json)                              # ④
        results[step] = executor.dispatch_tool(tool_name, args)

    return {
        "fidelity": executor.fidelity,
        "steps_replayed": len(results),
        "model_pin_warning": (                                    # ⑤
            cp.system_fingerprint != _get_live_fingerprint()
        ),
    }
