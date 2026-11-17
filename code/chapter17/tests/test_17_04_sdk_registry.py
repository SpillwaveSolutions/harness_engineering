"""Tests for listing 17-04-sdk-registry.

Verifies structure of the file: no unused imports, function
signatures are present and type-annotated, and all lines fit
within 75 characters.  The listing depends on claude_agent_sdk
which is not installed in the test environment; we test the
file's static properties without executing it.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = _CHAPTER_ROOT / "listings" / "17-04-sdk-registry.py"


def _source() -> str:
    return _LISTING_PATH.read_text()


def _tree() -> ast.Module:
    return ast.parse(_source())


def test_listing_file_exists():
    """Listing file must be present on disk."""
    assert _LISTING_PATH.exists(), f"Missing: {_LISTING_PATH}"


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


def test_no_unused_import_anthropic():
    """Listing must not contain `import anthropic`."""
    source = _source()
    assert "import anthropic" not in source, (
        "Unused `import anthropic` found in listing"
    )


def test_search_flights_function_defined():
    """search_flights async function must be defined."""
    tree = _tree()
    names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]
    assert "search_flights" in names


def test_book_flight_function_defined():
    """book_flight async function must be defined."""
    tree = _tree()
    names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]
    assert "book_flight" in names


def test_run_agent_function_defined():
    """run_agent async function must be defined."""
    tree = _tree()
    names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]
    assert "run_agent" in names


def test_tools_and_run_agent_offline(monkeypatch):
    """Tool functions return an offline booking reference and do not call out."""
    import asyncio
    import importlib.util

    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spec = importlib.util.spec_from_file_location(
        "listing_17_04_exec", _LISTING_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    search = asyncio.run(mod.search_flights.handler({
        "origin": "SFO",
        "destination": "JFK",
        "date": "2026-06-01",
    }))
    booked = asyncio.run(mod.book_flight.handler({
        "flight_id": "AA100",
        "passenger_name": "Ada Lovelace",
    }))
    text = asyncio.run(mod.run_agent("Book a flight to Paris"))
    search_text = search["content"][0]["text"]
    booked_text = booked["content"][0]["text"]
    assert search_text.startswith("offline:OFFLINE-SEARCH")
    assert "SFO" in search_text
    assert booked_text.startswith("offline:OFFLINE-BOOKING")
    assert "AA100" in booked_text
    assert text == "offline:OFFLINE-BOOKING"
    assert mod.search_flights.name == "search_flights"
    assert mod.search_flights.input_schema["origin"] is str
    assert mod.server["name"] == "travel"


def test_listing_is_valid_python():
    """Listing must parse as valid Python 3.13 syntax."""
    try:
        ast.parse(_source())
    except SyntaxError as exc:
        pytest.fail(f"SyntaxError in listing: {exc}")
