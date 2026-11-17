"""Tests for listing 13-01-otel-model-span (§13.1).

The listing establishes the tracer-provider bootstrap pattern and defines
call_model_with_span. Both require a live OTLP endpoint at module load time
(via the BatchSpanProcessor constructor). We patch the exporter and the
Anthropic client so the module can be exercised without network access.

§13.1 prose claim: the listing uses gen_ai.operation.name='chat',
gen_ai.provider.name='anthropic', gen_ai.request.model='claude-sonnet-4-6',
and gen_ai.conversation.id to link turns.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def test_listing_defines_call_model_with_span():
    """§13.1: listing must define call_model_with_span after patching OTLP deps."""
    otlp_exporter_mock = MagicMock()
    otlp_mod_mock = MagicMock()
    otlp_mod_mock.OTLPSpanExporter.return_value = otlp_exporter_mock

    with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"}), \
         patch.dict(sys.modules, {
             "opentelemetry.exporter.otlp.proto.http.trace_exporter": otlp_mod_mock,
             "anthropic": MagicMock(),
         }):
        path = LISTINGS_DIR / "13-01-otel-model-span.py"
        if not path.exists():
            pytest.fail(f"listing not found at {path}")
        spec = importlib.util.spec_from_file_location("listing_13_01", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_13_01"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    assert callable(mod.call_model_with_span), (
        "call_model_with_span must be callable"
    )


def test_model_name_is_claude_sonnet_4_6():
    """§13.1: model name in span attribute must be 'claude-sonnet-4-6' (CLAUDE.md §16)."""
    otlp_mod_mock = MagicMock()
    otlp_mod_mock.OTLPSpanExporter.return_value = MagicMock()

    with patch.dict(os.environ, {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"}), \
         patch.dict(sys.modules, {
             "opentelemetry.exporter.otlp.proto.http.trace_exporter": otlp_mod_mock,
             "anthropic": MagicMock(),
         }):
        path = LISTINGS_DIR / "13-01-otel-model-span.py"
        if not path.exists():
            pytest.fail(f"listing not found at {path}")
        spec = importlib.util.spec_from_file_location("listing_13_01_b", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_13_01_b"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    import inspect
    src = inspect.getsource(mod.call_model_with_span)
    assert "claude-sonnet-4-6" in src, (
        "call_model_with_span must reference 'claude-sonnet-4-6'"
    )


def test_offline_call_returns_fake_usage(load_listing, monkeypatch):
    """Missing API key returns a fake response and does not call the API."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    listing = load_listing("13-01-otel-model-span")
    response = listing.call_model_with_span(
        [{"role": "user", "content": "hi"}],
        "conv-1",
    )
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 8

