"""Tests for listing 17-02-coverage-table.

Verifies that COVERAGE_TABLE contains all thirteen patterns across
the five harness, five workflow, and three composite categories,
and that every cell contains a valid coverage literal.
"""

from __future__ import annotations

import importlib.util
import pathlib

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = _CHAPTER_ROOT / "listings" / "17-02-coverage-table.py"

_spec = importlib.util.spec_from_file_location(
    "listing_17_02", _LISTING_PATH
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

COVERAGE_TABLE = _mod.COVERAGE_TABLE
PatternCoverage = _mod.PatternCoverage

VALID_COVERAGE = {"OTS", "CONF", "BYO"}
VALID_CATEGORIES = {"harness", "workflow", "composite"}

EXPECTED_PATTERNS = {
    # harness
    "Progressive disclosure",
    "Isolation",
    "Spec-first",
    "Mechanical enforcement",
    "Integrated feedback",
    # workflow
    "Prompt chaining",
    "Routing",
    "Parallelization",
    "Orchestrator-workers",
    "Evaluator-optimizer",
    # composite
    "Hub-and-spoke",
    "Dual-agent handoff",
    "Generator-critic-arbiter",
}


def test_table_has_thirteen_rows():
    """Coverage table must contain exactly thirteen patterns."""
    assert len(COVERAGE_TABLE) == 13


def test_all_expected_patterns_present():
    """Every named pattern must appear in the table."""
    actual = {row.pattern for row in COVERAGE_TABLE}
    assert actual == EXPECTED_PATTERNS


def test_all_cells_are_valid_coverage_literals():
    """Every OTS/CONF/BYO cell must be a valid literal."""
    for row in COVERAGE_TABLE:
        assert row.claude_sdk in VALID_COVERAGE, (
            f"{row.pattern}: claude_sdk={row.claude_sdk!r}"
        )
        assert row.deep_agents in VALID_COVERAGE, (
            f"{row.pattern}: deep_agents={row.deep_agents!r}"
        )
        assert row.google_adk in VALID_COVERAGE, (
            f"{row.pattern}: google_adk={row.google_adk!r}"
        )


def test_all_categories_are_valid():
    """Category field must be one of harness/workflow/composite."""
    for row in COVERAGE_TABLE:
        assert row.category in VALID_CATEGORIES, (
            f"{row.pattern}: category={row.category!r}"
        )


def test_five_harness_patterns():
    """Table must include exactly five harness-category rows."""
    harness_rows = [r for r in COVERAGE_TABLE if r.category == "harness"]
    assert len(harness_rows) == 5


def test_five_workflow_patterns():
    """Table must include exactly five workflow-category rows."""
    workflow_rows = [
        r for r in COVERAGE_TABLE if r.category == "workflow"
    ]
    assert len(workflow_rows) == 5


def test_three_composite_patterns():
    """Table must include exactly three composite-category rows."""
    composite_rows = [
        r for r in COVERAGE_TABLE if r.category == "composite"
    ]
    assert len(composite_rows) == 3


def test_generator_critic_arbiter_is_byo_for_all():
    """Generator-critic-arbiter is BYO across all three frameworks."""
    gca = next(
        r for r in COVERAGE_TABLE
        if r.pattern == "Generator-critic-arbiter"
    )
    assert gca.claude_sdk == "BYO"
    assert gca.deep_agents == "BYO"
    assert gca.google_adk == "BYO"


def test_no_line_exceeds_75_chars():
    """All lines in the listing file must be within 75 characters."""
    lines = _LISTING_PATH.read_text().splitlines()
    violations = [
        (i + 1, len(line), line)
        for i, line in enumerate(lines)
        if len(line) > 75
    ]
    assert violations == [], (
        "Lines exceeding 75 chars:\n"
        + "\n".join(
            f"  line {n} ({length} chars): {text}"
            for n, length, text in violations
        )
    )
