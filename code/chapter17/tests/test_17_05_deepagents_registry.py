"""Tests for listing 17-05-deepagents-registry.

Verifies the listing is valid Python, fits within 75-char width,
and demonstrates the key structural property: the model string
uses the provider:model format for provider portability.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = (
    _CHAPTER_ROOT / "listings" / "17-05-deepagents-registry.py"
)


def _source() -> str:
    return _LISTING_PATH.read_text()


def test_listing_file_exists():
    """Listing file must be present on disk."""
    assert _LISTING_PATH.exists(), f"Missing: {_LISTING_PATH}"


def test_listing_is_valid_python():
    """Listing must parse as valid Python 3.13 syntax."""
    try:
        ast.parse(_source())
    except SyntaxError as exc:
        pytest.fail(f"SyntaxError in listing: {exc}")


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


def test_provider_model_string_format_used():
    """Model string must use provider:model format for portability."""
    source = _source()
    assert "anthropic:claude-sonnet-4-6" in source, (
        "Expected provider:model string 'anthropic:claude-sonnet-4-6'"
    )


def test_tools_return_offline_references():
    """Defined tools return an offline reference and the agent is built locally."""
    import asyncio
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "listing_17_05_exec", _LISTING_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    search = asyncio.run(
        mod.search_flights("SFO", "JFK", "2026-06-01")
    )
    booked = asyncio.run(mod.book_flight("AA100", "Ada Lovelace"))
    assert search["reference"] == "OFFLINE-SEARCH"
    assert booked["reference"] == "OFFLINE-BOOKING"
    assert mod.agent is not None


def test_create_deep_agent_call_present():
    """create_deep_agent call must be present in listing."""
    source = _source()
    assert "create_deep_agent" in source
