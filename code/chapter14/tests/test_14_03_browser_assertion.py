"""Tests for listing 14-03-browser-assertion (§14.5).

Verifies:
  - Module defines verify_booking_ui callable.
  - verify_booking_ui has correct signature (flight_id, passenger_name).
  - Module imports cleanly even without playwright installed
    (patched out for CI).
"""

from __future__ import annotations

import importlib.util
import inspect
import pathlib
import sys
from unittest.mock import MagicMock, patch

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    """Load the listing with playwright patched out."""
    playwright_mock = MagicMock()
    path = LISTINGS_DIR / "14-03-browser-assertion.py"
    with patch.dict(sys.modules, {
        "playwright": playwright_mock,
        "playwright.sync_api": playwright_mock,
    }):
        spec = importlib.util.spec_from_file_location(
            "listing_14_03", path
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["listing_14_03"] = mod
        spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_defines_verify_booking_ui():
    """§14.5: listing must define callable verify_booking_ui."""
    mod = _load_module()
    assert hasattr(mod, "verify_booking_ui")
    assert callable(mod.verify_booking_ui)


def test_verify_booking_ui_offline_without_browser(monkeypatch):
    """Without the live flag, return the offline dict and do not launch a browser."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    mod = _load_module()
    result = mod.verify_booking_ui("AA100", "Ada Lovelace")
    assert result == {
        "status": "offline",
        "flight_id": "AA100",
        "passenger_name": "Ada Lovelace",
    }


def test_verify_booking_ui_signature():
    """§14.5: verify_booking_ui must accept flight_id and passenger_name."""
    mod = _load_module()
    sig = inspect.signature(mod.verify_booking_ui)
    params = list(sig.parameters.keys())
    assert "flight_id" in params
    assert "passenger_name" in params
