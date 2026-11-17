"""01-01-search-cap — the SWE-agent search-cap primitive (representative sketch).

Chapter 1 §1.2 introduces this as the first ACI primitive: a search tool that
refuses to flood the context window with results above a fixed cap. The prose
shows the public surface (`search_files`) and a stub `_run_grep`. This runnable
listing fills in `_run_grep` with a small pure-Python implementation so the
listing executes end-to-end under pytest.

Behavior contract — matches the prose:
  search_files(query, repo_root, max_results=50) returns one of two shapes:
    {"status": "ok",                "results": [...]}            # 0..max_results hits
    {"status": "too_many_results",  "count": N, "suggestion": "..."}  # N > max_results

The cap protects context budget: above max_results the tool refuses output and
tells the caller to narrow the query. This is the output-discipline pattern
Chapter 9 (§9.6) develops in full.
"""

from __future__ import annotations

import pathlib
from typing import Any


def search_files(query: str, repo_root: str, max_results: int = 50) -> dict[str, Any]:
    """Search repository files for query. Returns at most max_results matches.

    If the search would return more than max_results, the results are rejected
    and a suggestion to narrow the query is returned instead. This keeps
    context-window pressure bounded regardless of repo size.
    """
    raw_hits = _run_grep(query, repo_root)

    if len(raw_hits) > max_results:
        return {
            "status": "too_many_results",
            "count": len(raw_hits),
            "suggestion": (
                f"Query matched {len(raw_hits)} files. "
                "Narrow the search (e.g., add a file extension or subdirectory)."
            ),
        }

    return {"status": "ok", "results": raw_hits}


def _run_grep(query: str, repo_root: str) -> list[dict[str, Any]]:
    """Walk repo_root and return every (file, line_number, line) where `query`
    appears as a substring on the line.

    Pure-Python grep: keeps the listing self-contained (no subprocess to ripgrep
    or system grep, so it runs the same on every CI environment). Skips binary
    files and unreadable paths silently — a real harness would surface those as
    a separate diagnostic channel, but for a teaching listing we keep the
    failure mode quiet so the cap behavior stays in focus.
    """
    hits: list[dict[str, Any]] = []
    root = pathlib.Path(repo_root)

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if query in line:
                hits.append(
                    {
                        "file": str(path.relative_to(root)),
                        "line": line_number,
                        "text": line,
                    }
                )
    return hits


def main() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as root:
        note = pathlib.Path(root) / "notes.txt"
        note.write_text("pack a bag\nfind a flight\n", encoding="utf-8")
        found = search_files("flight", root, max_results=50)
        print(found["status"])
        print(found["results"][0]["text"])


if __name__ == "__main__":
    main()
