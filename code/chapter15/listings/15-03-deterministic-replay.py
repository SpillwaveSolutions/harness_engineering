from __future__ import annotations

import importlib.util
import json
import logging
import sys
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def _load_checkpoint_cls():
    """Load HarnessCheckpoint from the sibling checkpoint listing."""
    path = Path(__file__).resolve().parent / "15-02-checkpoint-writer.py"
    name = "ch15_checkpoint_writer"
    if name in sys.modules:
        return sys.modules[name].HarnessCheckpoint
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.HarnessCheckpoint


HarnessCheckpoint = _load_checkpoint_cls()

class ReplayExecutor:
    """Replays a checkpoint stream without live tool calls."""

    def __init__(
        self,
        checkpoint: HarnessCheckpoint,  # ①
        model_version: str = "claude-sonnet-4-6",
    ):
        self.checkpoint = checkpoint
        self.expected_model = model_version
        self._replay_hits: int = 0
        self._live_hits: int = 0

    def _verify_model_pin(self, live_fingerprint: str) -> None:  # ②
        if live_fingerprint != self.checkpoint.system_fingerprint:
            log.warning(
                "system_fingerprint changed: checkpoint=%s live=%s — "
                "replay may diverge",
                self.checkpoint.system_fingerprint,
                live_fingerprint,
            )

    def dispatch_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        if key in self.checkpoint.tool_results:          # ③
            self._replay_hits += 1
            return self.checkpoint.tool_results[key]
        self._live_hits += 1
        raise ValueError(
            f"No recorded response for {tool_name} — "
            "this call did not appear in the original run. "
            "Live call blocked in replay mode."
        )

    @property
    def fidelity(self) -> float:
        total = self._replay_hits + self._live_hits
        return self._replay_hits / total if total else 1.0
