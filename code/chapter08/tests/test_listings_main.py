"""Each listing's __main__ demo exits 0 without a network call."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LISTINGS = [
    "08-03-claude-tool-choice.py",
    "08-03-langchain-tool-choice.py",
    "08-04-semantic-validator.py",
    "08-05-claude-policy.py",
    "08-05-langchain-policy-middleware.py",
    "08-06-claude-prehook.py",
    "08-06-langchain-prehook.py",
    "08-07-claude-posthook.py",
    "08-07-date-normalize.py",
    "08-07-langchain-posthook.py",
    "08-08-validation-retry.py",
    "08-10-claude-integrated.py",
    "08-10-langchain-integrated.py",
]


@pytest.mark.parametrize("name", LISTINGS)
def test_main_exits_zero(name: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "listings" / name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
