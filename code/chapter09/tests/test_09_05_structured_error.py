"""Tests for 09-05-structured-error: verifies cancel_booking comment fixed.

Per action_item index 6 in evals/runs/2026-06-13T19:36:12Z-ch09/verdict.json:
'Fix misleading inline comment on line 30: search_flights -> cancel_booking.'

CodeTestPlan:
- Test that the listing source no longer contains the wrong comment string.
- Test that it contains the correct comment string.
- Test that ToolError validates all four ErrorCategory values.
- Test that make_tool_error correctly sets is_retryable=True only for
  'transient' category.
- Test that the ToolError Pydantic model rejects an invalid category.
"""

from __future__ import annotations

import pathlib

import pytest
from pydantic import ValidationError

LISTING_PATH = (
    pathlib.Path(__file__).parent.parent / "listings" / "09-05-structured-error.py"
)


def test_wrong_comment_absent() -> None:
    """Source must not contain the old misleading comment naming search_flights."""
    source = LISTING_PATH.read_text()
    assert "search_flights tool error" not in source, (
        "The comment still says 'search_flights tool error'; "
        "it should read 'cancel_booking tool error' after the fix."
    )


def test_correct_comment_present() -> None:
    """Source must contain the corrected comment naming cancel_booking."""
    source = LISTING_PATH.read_text()
    assert "cancel_booking tool error" in source, (
        "Expected 'cancel_booking tool error' in comment; not found."
    )


def test_listing_loads(load_listing) -> None:
    """The listing must load or skip cleanly (never hard-fail)."""
    module = load_listing("09-05-structured-error")
    public = [n for n in dir(module) if not n.startswith("_")]
    assert public, "listing loaded but exposes no public names"


def test_make_tool_error_transient_is_retryable(load_listing) -> None:
    """make_tool_error('transient', ...) must set is_retryable=True."""
    module = load_listing("09-05-structured-error")
    result = module.make_tool_error(
        category="transient",
        message="rate limited",
        user_message="Please try again in a moment.",
    )
    assert result["is_retryable"] is True
    assert result["error_category"] == "transient"


def test_make_tool_error_business_not_retryable(load_listing) -> None:
    """make_tool_error('business', ...) must set is_retryable=False."""
    module = load_listing("09-05-structured-error")
    result = module.make_tool_error(
        category="business",
        message="non-refundable fare",
        user_message="This booking cannot be cancelled.",
    )
    assert result["is_retryable"] is False
    assert result["error_category"] == "business"


def test_make_tool_error_all_categories(load_listing) -> None:
    """All four ErrorCategory values are accepted by make_tool_error."""
    module = load_listing("09-05-structured-error")
    for cat in ("transient", "validation", "permission", "business"):
        result = module.make_tool_error(
            category=cat,
            message=f"{cat} error",
            user_message="Something went wrong.",
        )
        assert result["error_category"] == cat


def test_cancel_booking_offline_paths(load_listing) -> None:
    module = load_listing("09-05-structured-error")
    blocked = module.cancel_booking("NR-100")
    assert blocked["error_category"] == "business"
    assert blocked["is_retryable"] is False
    assert "NR-100" in blocked["message"]
    assert module.cancel_booking("BK-100") == {
        "booking_id": "BK-100",
        "status": "cancelled",
    }


def test_tool_error_rejects_invalid_category(load_listing) -> None:
    """ToolError must raise ValidationError for an unknown error_category."""
    module = load_listing("09-05-structured-error")
    ToolError = module.ToolError
    with pytest.raises(ValidationError):
        ToolError(
            error_category="unknown",
            is_retryable=False,
            message="bad",
            user_message="bad",
        )
