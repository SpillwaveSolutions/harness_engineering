"""Tests for listing 13-05-langfuse-setup.

setup_langfuse() returns None unless both Langfuse keys are set. Import
does not call get_client().
"""

from __future__ import annotations


def test_import_does_not_require_keys(load_listing, monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    module = load_listing("13-05-langfuse-setup")
    assert hasattr(module, "setup_langfuse")


def test_setup_langfuse_offline_returns_none(load_listing, monkeypatch, capsys):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    module = load_listing("13-05-langfuse-setup")
    assert module.setup_langfuse() is None
    captured = capsys.readouterr()
    assert "LANGFUSE_PUBLIC_KEY" in captured.err
    assert "LANGFUSE_SECRET_KEY" in captured.err


def test_setup_langfuse_calls_get_client_when_keys_present(load_listing, monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    module = load_listing("13-05-langfuse-setup")
    sentinel = object()
    monkeypatch.setattr(module, "get_client", lambda: sentinel)
    assert module.setup_langfuse() is sentinel
