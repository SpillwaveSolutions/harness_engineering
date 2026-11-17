"""Every chapter 8 listing imports and exposes a public name."""

from __future__ import annotations

import pytest

CHAPTER_8_LISTINGS = [
    "08-03-claude-tool-choice",
    "08-03-langchain-tool-choice",
    "08-04-semantic-validator",
    "08-05-claude-policy",
    "08-05-langchain-policy-middleware",
    "08-06-claude-prehook",
    "08-06-langchain-prehook",
    "08-07-claude-posthook",
    "08-07-langchain-posthook",
    "08-07-date-normalize",
    "08-08-validation-retry",
    "08-10-claude-integrated",
    "08-10-langchain-integrated",
]


@pytest.mark.parametrize("listing_id", CHAPTER_8_LISTINGS)
def test_listing_imports(listing_id: str, load_listing) -> None:
    module = load_listing(listing_id)
    public_names = [name for name in dir(module) if not name.startswith("_")]
    assert public_names
