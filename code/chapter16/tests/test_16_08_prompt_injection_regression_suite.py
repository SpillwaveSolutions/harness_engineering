"""Tests for listing 16-08-prompt-injection-regression-suite.

Verifies that ALL_CASES covers context, tool, and memory tiers,
that test_injection_defense correctly blocks expected payloads,
and that promotion_gate_safety_lane returns PASS when all
defenses hold.
"""

import importlib.util
import pathlib
import sys

import pytest

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
if str(_CHAPTER_ROOT) not in sys.path:
    sys.path.insert(0, str(_CHAPTER_ROOT))

from harness.travel_booking import TravelBookingHarness

_LISTING_PATH = (
    _CHAPTER_ROOT
    / "listings"
    / "16-08-prompt-injection-regression-suite.py"
)
_spec = importlib.util.spec_from_file_location(
    "listing_16_08", _LISTING_PATH
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

Boundary = _mod.Boundary
InjectionTestCase = _mod.InjectionTestCase
CONTEXT_CASES = _mod.CONTEXT_CASES
TOOL_CASES = _mod.TOOL_CASES
MEMORY_CASES = _mod.MEMORY_CASES
ALL_CASES = _mod.ALL_CASES
promotion_gate_safety_lane = _mod.promotion_gate_safety_lane


@pytest.fixture
def harness(tmp_path):
    return TravelBookingHarness(
        model="claude-sonnet-4-6",
        tenant_id="test-tenant",
        storage_path=tmp_path,
    )


def test_all_cases_covers_three_tiers():
    """ALL_CASES must include context, tool, and memory cases."""
    boundaries = {c.boundary for c in ALL_CASES}
    assert Boundary.CONTEXT in boundaries
    assert Boundary.TOOL in boundaries
    assert Boundary.MEMORY in boundaries


def test_all_cases_non_empty():
    """ALL_CASES must contain at least one test case per tier."""
    assert len(CONTEXT_CASES) >= 1
    assert len(TOOL_CASES) >= 1
    assert len(MEMORY_CASES) >= 1


@pytest.mark.parametrize(
    "case",
    ALL_CASES,
    ids=[c.id for c in ALL_CASES],
)
def test_each_case_has_required_fields(case):
    """Each InjectionTestCase must have id, boundary, payload."""
    assert case.id
    assert case.boundary
    assert case.attack_payload


@pytest.mark.parametrize(
    "case",
    [c for c in ALL_CASES if c.expected_blocked],
    ids=[c.id for c in ALL_CASES if c.expected_blocked],
)
def test_expected_blocked_cases_are_blocked(harness, case):
    """Cases marked expected_blocked=True must be blocked."""
    result = harness.run_security_test(case)
    assert result.blocked, (
        f"[{case.id}] defense failed: {case.description}\n"
        f"Boundary: {case.boundary.value}\n"
        f"Reached model: {result.reached_model}"
    )


def test_promotion_gate_safety_lane_returns_pass(harness):
    """promotion_gate_safety_lane must return PASS verdict."""
    gate_result = promotion_gate_safety_lane(harness)
    assert gate_result["verdict"] == "PASS", (
        f"Safety lane failed: {gate_result['failed_cases']}"
    )
    assert gate_result["total"] == len(ALL_CASES)


def test_injection_test_case_dataclass_fields():
    """InjectionTestCase dataclass must have all required fields."""
    case = InjectionTestCase(
        id="test-01",
        boundary=Boundary.CONTEXT,
        description="test case",
        attack_payload={"user_input": "hello"},
        expected_blocked=False,
    )
    assert case.id == "test-01"
    assert case.boundary == Boundary.CONTEXT
    assert case.expected_blocked is False
