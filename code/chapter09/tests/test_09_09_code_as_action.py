"""Offline code-as-action returns a one-line summary."""

from __future__ import annotations

import os

import pytest


def test_offline_summary(load_listing, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("09-09-code-as-action")
    assert module.run_code_as_action("transfer bookings") == (
        "offline: transferred 0 records (0 success, 0 errors)"
    )


@pytest.mark.skipif(
    os.environ.get("HARNESS_LIVE_API") != "1",
    reason="set HARNESS_LIVE_API=1 to exercise the live API",
)
def test_live_summary_is_text(load_listing) -> None:
    module = load_listing("09-09-code-as-action")
    text = module.run_code_as_action("Report totals only.")
    assert isinstance(text, str)
    assert text
