"""Tests for listing 13-02-seven-span-kinds (§13.2).

The listing demonstrates the structural invariant: every execute_tool span is
a child of the invoke_agent span that initiated the turn, not a sibling. The
parent invoke_agent span uses SpanKind.CLIENT.

§13.2 prose claim: seven span kinds cover every decision surface the harness
owns; the invoke_agent span uses SpanKind.CLIENT; span names follow the pattern
'chat claude-sonnet-4-6' and 'execute_tool <tool_name>'.
"""

from __future__ import annotations

import importlib.util
import inspect
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_listing() -> object:
    """Load listing 13-02 with Anthropic and OTel tracer patched out."""
    path = LISTINGS_DIR / "13-02-seven-span-kinds.py"
    if not path.exists():
        pytest.fail(f"listing not found at {path}")

    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_span.__enter__ = MagicMock(return_value=mock_span)
    mock_span.__exit__ = MagicMock(return_value=False)
    mock_tracer.start_as_current_span.return_value = mock_span

    mock_trace_mod = MagicMock()
    mock_trace_mod.get_tracer.return_value = mock_tracer

    module_name = f"listing_13_02_{id(mock_tracer)}"
    with patch.dict(sys.modules, {
        "anthropic": MagicMock(),
        "opentelemetry": MagicMock(),
        "opentelemetry.trace": mock_trace_mod,
    }):
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    return mod


def test_listing_defines_run_booking_step():
    """§13.2: listing must define run_booking_step as callable."""
    mod = _load_listing()
    assert hasattr(mod, "run_booking_step"), (
        "listing 13-02 must define run_booking_step"
    )
    assert callable(mod.run_booking_step), (
        "run_booking_step must be callable"
    )


def test_span_name_contains_claude_sonnet_4_6():
    """§13.2: the chat span name must contain 'claude-sonnet-4-6'."""
    mod = _load_listing()
    src = inspect.getsource(mod.run_booking_step)
    assert "claude-sonnet-4-6" in src, (
        "run_booking_step must reference 'claude-sonnet-4-6' in the chat span name"
    )


def test_span_kind_client_used_for_invoke_agent():
    """§13.2: invoke_agent span must use SpanKind.CLIENT."""
    mod = _load_listing()
    src = inspect.getsource(mod.run_booking_step)
    assert "SpanKind.CLIENT" in src, (
        "invoke_agent span must specify SpanKind.CLIENT"
    )


def test_run_booking_step_returns_offline_dict(load_listing, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    listing = load_listing("13-02-seven-span-kinds")
    result = listing.run_booking_step(
        "conv-1",
        [{"role": "user", "content": "hi"}],
    )
    assert result["conversation_id"] == "conv-1"
    assert result["status"] == "ok"
    assert result["tools"][0]["tool"] == "search_flights"
    assert result["tools"][0]["status"] == "ok"

