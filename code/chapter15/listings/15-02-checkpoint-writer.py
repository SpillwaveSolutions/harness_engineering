import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HarnessCheckpoint:
    session_id: str
    step: str                         # ① which feature or plan step
    tool_results: dict[str, Any]      # ② captured inputs + outputs
    model_version: str                # ③ e.g. "claude-sonnet-4-6"
    system_fingerprint: str           # ③ backend config hash
    cost_tokens_in: int
    cost_tokens_out: int
    cost_usd: float
    git_sha: str                      # ④ last clean commit
    transcript_hash: str              # ⑤ hash of serialized history
    timestamp: float = field(default_factory=time.time)

    def write(self, checkpoint_dir: Path) -> Path:
        path = checkpoint_dir / f"{self.session_id}_{self.step}.json"
        path.write_text(json.dumps(asdict(self), indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "HarnessCheckpoint":
        return cls(**json.loads(path.read_text()))

    @classmethod
    def exists(cls, checkpoint_dir: Path, session_id: str, step: str) -> bool:
        return (checkpoint_dir / f"{session_id}_{step}.json").exists()
