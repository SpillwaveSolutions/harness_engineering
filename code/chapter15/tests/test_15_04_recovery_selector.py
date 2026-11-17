"""Tests for listing 15-04-recovery-selector (§15.4).

Verifies all four branches of select_recovery:
  - ABANDON when checkpoint_corrupt is True.
  - ABANDON when budget_exhausted is True.
  - BRANCH when is_debugging is True (and no corruption/budget issues).
  - RESUME for transient error types (timeout, rate_limit, network, restart).
  - ABANDON for non-transient errors (e.g. auth_failure, logic_error).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

LISTINGS_DIR = Path(__file__).parent.parent / "listings"


def _load_module():
    path = LISTINGS_DIR / "15-04-recovery-selector.py"
    spec = importlib.util.spec_from_file_location("listing_15_04", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_15_04"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_module_imports():
    """§15.4: listing imports without error; RecoveryAction defined."""
    mod = _load_module()
    assert hasattr(mod, "select_recovery")
    assert hasattr(mod, "RecoveryAction")


def test_abandon_on_corrupt_checkpoint():
    """§15.4 branch ①: corrupt checkpoint → ABANDON regardless of error type."""
    mod = _load_module()
    result = mod.select_recovery(
        error_type="timeout",
        budget_exhausted=False,
        checkpoint_corrupt=True,
        is_debugging=False,
    )
    assert result == mod.RecoveryAction.ABANDON


def test_abandon_on_budget_exhausted():
    """§15.4 branch ①: budget exhausted → ABANDON."""
    mod = _load_module()
    result = mod.select_recovery(
        error_type="network",
        budget_exhausted=True,
        checkpoint_corrupt=False,
        is_debugging=False,
    )
    assert result == mod.RecoveryAction.ABANDON


def test_branch_when_debugging():
    """§15.4 branch ②: is_debugging=True → BRANCH (fault isolation)."""
    mod = _load_module()
    result = mod.select_recovery(
        error_type="timeout",
        budget_exhausted=False,
        checkpoint_corrupt=False,
        is_debugging=True,
    )
    assert result == mod.RecoveryAction.BRANCH


@pytest.mark.parametrize("error_type", [
    "timeout", "rate_limit", "network", "restart"
])
def test_resume_for_transient_errors(error_type):
    """§15.4 branch ③: transient error types → RESUME."""
    mod = _load_module()
    result = mod.select_recovery(
        error_type=error_type,
        budget_exhausted=False,
        checkpoint_corrupt=False,
        is_debugging=False,
    )
    assert result == mod.RecoveryAction.RESUME


@pytest.mark.parametrize("error_type", [
    "auth_failure", "logic_error", "permission_denied", "unknown"
])
def test_abandon_for_non_transient_errors(error_type):
    """§15.4 branch ④: non-transient errors → ABANDON."""
    mod = _load_module()
    result = mod.select_recovery(
        error_type=error_type,
        budget_exhausted=False,
        checkpoint_corrupt=False,
        is_debugging=False,
    )
    assert result == mod.RecoveryAction.ABANDON
