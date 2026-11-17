"""Tests for listing 08-07-date-normalize.

Pure stdlib (re + datetime) — fully testable. Covers the load-bearing claims
from §8.7's date-normalization post-hook:

1. A 4-digit-year US-format date (MM/DD/YYYY) is converted to ISO-8601.
2. A 2-digit-year US-format date is widened with the `20` prefix.
3. Input without an MM/DD/YYYY substring is returned unchanged (no-op path).
"""

from __future__ import annotations


def test_four_digit_year_normalized(load_listing) -> None:
    """'05/15/2026' becomes '2026-05-15'."""
    module = load_listing("08-07-date-normalize")
    assert module.normalize_date("05/15/2026") == "2026-05-15"


def test_two_digit_year_widened(load_listing) -> None:
    """'5/15/26' becomes '2026-05-15' via the 2-digit-year branch."""
    module = load_listing("08-07-date-normalize")
    assert module.normalize_date("5/15/26") == "2026-05-15"


def test_non_matching_input_unchanged(load_listing) -> None:
    """Strings without an MM/DD/YYYY substring are returned verbatim."""
    module = load_listing("08-07-date-normalize")
    assert module.normalize_date("already-iso-2026-05-15") == "already-iso-2026-05-15"
