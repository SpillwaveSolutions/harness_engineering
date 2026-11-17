"""Every chapter 9 Python listing imports and exposes a public name."""

from __future__ import annotations

import pytest

CHAPTER_9_LISTINGS = [
    "09-02-tool-description",
    "09-05-structured-error",
    "09-07-schema-driven-tool",
    "09-09-code-as-action",
    "09-16-capability-registry",
]


@pytest.mark.parametrize("listing_id", CHAPTER_9_LISTINGS)
def test_listing_imports(listing_id: str, load_listing) -> None:
    module = load_listing(listing_id)
    public = [name for name in dir(module) if not name.startswith("_")]
    assert public
