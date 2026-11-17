"""Tests for listing 17-08-migration-diff.

Verifies that the AFTER block's bare `await` is wrapped in an
async function (no module-scope await), that the listing parses
without SyntaxError, and that all lines fit within 75 chars.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = (
    _CHAPTER_ROOT / "listings" / "17-08-migration-diff.py"
)


def _source() -> str:
    return _LISTING_PATH.read_text()


def _tree() -> ast.Module:
    return ast.parse(_source())


def test_listing_file_exists():
    """Listing file must be present on disk."""
    assert _LISTING_PATH.exists(), f"Missing: {_LISTING_PATH}"


def test_listing_is_valid_python():
    """Listing must parse as valid Python 3.13 syntax (no SyntaxError).

    The original listing had `result = await query(...)` at module
    scope, which is a SyntaxError in Python 3.13.  This test
    catches any regression.
    """
    try:
        ast.parse(_source())
    except SyntaxError as exc:
        pytest.fail(
            f"SyntaxError in listing (bare await at module scope?): {exc}"
        )


def test_no_bare_await_at_module_scope():
    """Await expressions must not appear at module scope.

    Any `await` in the listing must be inside an async function body.
    """
    tree = _tree()

    # Collect all Await nodes and their enclosing function depth
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(
            node.value, ast.Await
        ):
            # A bare `await x` as a statement at module level would
            # appear as an ast.Expr whose value is an ast.Await.
            # If we reach here we need to check it is inside a def.
            # ast.walk does not give us parent context, so we rely on
            # the compile check above; this assertion is belt-and-
            # suspenders for top-level await expressions.
            pytest.fail(
                "Bare `await` expression found as a top-level statement"
            )


def test_migration_tools_offline(monkeypatch):
    """Both tool functions and the migrated runner stay offline by default."""
    import asyncio
    import importlib.util

    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    spec = importlib.util.spec_from_file_location(
        "listing_17_08_exec", _LISTING_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    search = asyncio.run(
        mod.search_flights("SFO", "JFK", "2026-06-01")
    )
    booked = asyncio.run(mod.book_flight("AA100", "Ada Lovelace"))
    text = asyncio.run(mod.run_after_migration("Book AA100"))
    assert search["status"] == "offline"
    assert booked["passenger_name"] == "Ada Lovelace"
    assert text == "offline:OFFLINE-BOOKING"
    assert mod.agent is not None
    assert mod.server["name"] == "travel"


def test_run_after_migration_is_async_function():
    """run_after_migration must be defined as an async def."""
    tree = _tree()
    async_funcs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]
    assert "run_after_migration" in async_funcs, (
        "Expected async def run_after_migration(...) in listing"
    )


def test_no_line_exceeds_75_chars():
    """All lines in the listing file must be within 75 characters."""
    lines = _source().splitlines()
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
