"""Each listing's __main__ demo exits 0 without a network call."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LISTINGS = [
    "07-03-hybrid-rrf.py",
    "07-04-contextual-chunk.py",
    "07-05-cohere-rerank.py",
    "07-07-citations.py",
    "07-10-agentic-search.py",
    "07-14-routing-policy.py",
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
