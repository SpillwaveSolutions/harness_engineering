"""Each listing's __main__ demo exits 0 without a network call."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LISTINGS = [
    "06-03-mem0-extraction.py",
    "06-04-memory-directory.py",
    "06-06-saliency-eviction.py",
    "06-08-memory-subsystem.py",
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
