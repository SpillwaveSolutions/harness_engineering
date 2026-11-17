"""Tests for listing 01-01-search-cap (§1.2).

Pins the three branches of the search-cap primitive:
  - happy path: matches under the cap return {"status": "ok", "results": [...]}
  - cap path: matches over the cap return {"status": "too_many_results", count, suggestion}
  - empty path: zero matches return {"status": "ok", "results": []}

Each test builds a small file tree under tmp_path so the listing's pure-Python
_run_grep has something to walk.
"""

from __future__ import annotations

import pathlib


def _seed_repo(root: pathlib.Path, file_count: int, hit_line: str) -> None:
    """Create `file_count` files under root, each containing one matching line
    plus a non-matching line for noise."""
    for i in range(file_count):
        (root / f"file_{i:03d}.txt").write_text(
            f"unrelated content\n{hit_line}\nmore unrelated text\n"
        )


def test_happy_path_under_cap_returns_ok(load_listing, tmp_path):
    """§1.2: a query that produces fewer than max_results hits returns ok + the hits."""
    listing = load_listing("01-01-search-cap")
    _seed_repo(tmp_path, file_count=5, hit_line="needle in this line")

    result = listing.search_files("needle", str(tmp_path), max_results=50)

    assert result["status"] == "ok"
    assert len(result["results"]) == 5
    for hit in result["results"]:
        assert "needle" in hit["text"]
        assert hit["line"] == 2  # the matching line index within each file
        assert hit["file"].startswith("file_")


def test_cap_path_over_cap_returns_too_many(load_listing, tmp_path):
    """§1.2: above max_results the tool refuses results and asks the agent to narrow.

    This is the production-discipline rule the SWE-agent ablation measured:
    capping search output instead of flooding the context window."""
    listing = load_listing("01-01-search-cap")
    # Use a tight cap so we don't have to seed 51 files just to test the rule.
    _seed_repo(tmp_path, file_count=10, hit_line="needle line")

    result = listing.search_files("needle", str(tmp_path), max_results=3)

    assert result["status"] == "too_many_results"
    assert result["count"] == 10
    assert "Narrow" in result["suggestion"]
    assert "results" not in result  # cap branch explicitly suppresses results


def test_empty_path_zero_hits_returns_ok_with_empty_list(load_listing, tmp_path):
    """§1.2: zero matches is the ok branch with an empty results list,
    not the too_many_results branch."""
    listing = load_listing("01-01-search-cap")
    _seed_repo(tmp_path, file_count=3, hit_line="nothing of interest")

    result = listing.search_files("absent-query", str(tmp_path), max_results=50)

    assert result["status"] == "ok"
    assert result["results"] == []
