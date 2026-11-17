"""Tests for listing 10-03-sandbox-as-tool.

`build_sandbox_agent` must import without calling Modal. With
MODAL_TOKEN_ID unset it prints a message and returns an offline dict.
"""

from __future__ import annotations

import pytest


def test_module_imports(load_listing) -> None:
    module = load_listing("10-03-sandbox-as-tool")
    assert callable(module.build_sandbox_agent)


def test_offline_when_modal_token_unset(
    load_listing, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    module = load_listing("10-03-sandbox-as-tool")

    def _forbid_lookup(*args, **kwargs):
        raise AssertionError("modal.App.lookup must not run offline")

    monkeypatch.setattr(module.modal.App, "lookup", _forbid_lookup)
    result = module.build_sandbox_agent()
    assert result == {"status": "offline"}
    captured = capsys.readouterr()
    assert "MODAL_TOKEN_ID" in captured.err
    assert "offline" in captured.err
