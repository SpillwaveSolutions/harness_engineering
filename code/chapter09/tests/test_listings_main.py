"""Each listing's __main__ demo exits 0 without a network call."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LISTINGS = [
    "09-02-tool-description.py",
    "09-05-structured-error.py",
    "09-07-schema-driven-tool.py",
    "09-09-code-as-action.py",
    "09-16-capability-registry.py",
]


@pytest.mark.parametrize("name", LISTINGS)
def test_main_exits_zero(name: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "listings" / name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
