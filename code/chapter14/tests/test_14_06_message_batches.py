"""Tests for listing 14-06-message-batches (§14.10).

Verifies:
  - Module imports without NameError (JUDGE_SYSTEM_PROMPT and parse_verdict
    both defined).
  - submit_eval_batch and collect_batch_results are callable.
  - parse_verdict extracts label from a succeeded message.
  - collect_batch_results handles errored and expired result types.

Patches the Anthropic client to avoid live network calls.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    """Load listing 14-06 with anthropic patched."""
    mock_anthropic = MagicMock()

    path = LISTINGS_DIR / "14-06-message-batches.py"
    with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
        spec = importlib.util.spec_from_file_location(
            "listing_14_06", path
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_14_06"] = mod
        spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_imports_without_nameerror():
    """§14.10: JUDGE_SYSTEM_PROMPT and parse_verdict must be defined."""
    mod = _load_module()
    assert hasattr(mod, "JUDGE_SYSTEM_PROMPT"), (
        "JUDGE_SYSTEM_PROMPT must be defined"
    )
    assert hasattr(mod, "parse_verdict"), (
        "parse_verdict must be defined"
    )


def test_submit_eval_batch_is_callable():
    """§14.10: submit_eval_batch must be callable."""
    mod = _load_module()
    assert callable(mod.submit_eval_batch)


def test_collect_batch_results_is_callable():
    """§14.10: collect_batch_results must be callable."""
    mod = _load_module()
    assert callable(mod.collect_batch_results)


def test_parse_verdict_extracts_label():
    """§14.10: parse_verdict must return dict with label from message content."""
    import json

    mod = _load_module()
    payload = json.dumps(
        {"label": "PASS", "flight_id_valid": 5}
    )
    msg = MagicMock()
    msg.content = [MagicMock(text=payload)]
    result = mod.parse_verdict(msg)
    assert result.get("label") == "PASS"


def test_build_eval_requests_without_key(monkeypatch):
    """Request dicts are built with no API key and no client."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_module()
    mod.client = None
    requests = mod.build_eval_requests(
        [{"trace_id": "t1", "booking_output": "booked AA1"}]
    )
    assert requests == [{
        "custom_id": "t1",
        "params": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 512,
            "system": mod.JUDGE_SYSTEM_PROMPT,
            "messages": [{
                "role": "user",
                "content": "Evaluate booking output:\n\nbooked AA1",
            }],
        },
    }]
    assert mod.client is None


def test_submit_eval_batch_offline_without_key(monkeypatch):
    """No live client returns a deterministic batch id and does not call out."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mod = _load_module()
    mod.client = None
    batch_id = mod.submit_eval_batch(
        [{"trace_id": "t1", "booking_output": "booked AA1"}]
    )
    assert batch_id == "offline"


def test_collect_batch_results_handles_errored():
    """§14.10: errored results must produce EVAL_ERROR label."""
    mod = _load_module()
    api = MagicMock()
    errored_result = MagicMock()
    errored_result.custom_id = "trace-001"
    errored_result.result.type = "errored"
    errored_result.result.error.type = "overloaded_error"
    api.messages.batches.results.return_value = [errored_result]
    mod.client = api

    results = mod.collect_batch_results("batch-xyz")
    assert results["trace-001"]["label"] == "EVAL_ERROR"


def test_collect_batch_results_handles_expired():
    """§14.10: expired results must produce EVAL_EXPIRED label."""
    mod = _load_module()
    api = MagicMock()
    expired_result = MagicMock()
    expired_result.custom_id = "trace-002"
    expired_result.result.type = "expired"
    api.messages.batches.results.return_value = [expired_result]
    mod.client = api

    results = mod.collect_batch_results("batch-xyz")
    assert results["trace-002"]["label"] == "EVAL_EXPIRED"
