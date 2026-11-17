"""Grep and head over a corpus, jailed to corpus_dir.

Patterns are passed after `--`, so a leading dash is data.
Paths that resolve outside corpus_dir are refused.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import anthropic

_MAX_STDOUT = 4000


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def grep_corpus(pattern: str, corpus_dir: str) -> str:
    """Return paths under corpus_dir whose contents match pattern."""
    root = Path(corpus_dir).resolve()
    if not root.is_dir():
        return ""
    try:
        result = subprocess.run(
            [
                "grep",
                "-r",
                "-l",
                "-m",
                "3",
                "--",
                pattern,
                str(root),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ""
    kept: list[str] = []
    for line in result.stdout.splitlines():
        path = Path(line.strip())
        if line.strip() and _inside(root, path):
            kept.append(str(path.resolve()))
    return "\n".join(kept)[:_MAX_STDOUT]


def head_file(
    path: str, lines: int = 20, corpus_dir: str | None = None
) -> str:
    """Read the first N lines of a file that stays inside corpus_dir."""
    if corpus_dir is None:
        print(
            "corpus_dir is required; refusing to read an unjailed path",
            file=sys.stderr,
        )
        return ""
    root = Path(corpus_dir).resolve()
    target = Path(path).resolve()
    if not _inside(root, target) or not target.is_file():
        return ""
    count = _as_line_count(lines)
    try:
        result = subprocess.run(
            ["head", "-n", str(count), "--", str(target)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ""
    return result.stdout[:_MAX_STDOUT]


def _offline_search(query: str, corpus_dir: str) -> str:
    hits = grep_corpus(query, corpus_dir)
    parts: list[str] = []
    for hit in hits.splitlines():
        if hit:
            parts.append(head_file(hit, lines=5, corpus_dir=corpus_dir))
    summary = " ".join(part.strip() for part in parts if part.strip())
    if not summary:
        return "offline: no matching files"
    return summary[:240]


def _as_line_count(lines: object) -> int:
    """Accept only a real int. bool is rejected; other types are an error."""
    if isinstance(lines, bool) or not isinstance(lines, int):
        raise TypeError(
            f"lines must be an int, got {type(lines).__name__}"
        )
    if lines < 0:
        raise ValueError("lines must be >= 0")
    return lines


def _dispatch_tool(name: str, tool_input: dict, corpus_dir: str) -> str:
    """Run a tool. corpus_dir comes from the caller, never from the model."""
    if name == "grep_corpus":
        return grep_corpus(str(tool_input.get("pattern", "")), corpus_dir)
    if name == "head_file":
        try:
            count = _as_line_count(tool_input.get("lines", 20))
        except (TypeError, ValueError) as exc:
            return str(exc)
        return head_file(
            str(tool_input.get("path", "")),
            lines=count,
            corpus_dir=corpus_dir,
        )
    return ""


def agentic_search_agent(query: str, corpus_dir: str) -> str:
    """Grep, then head. The jail directory is the corpus_dir argument.

    The model may choose a pattern and a path. It cannot choose the
    directory those tools are allowed to touch.
    """
    tools = [
        {
            "name": "grep_corpus",
            "description": (
                "Search the configured corpus for files matching a pattern. "
                "The directory is fixed by the harness."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
        {
            "name": "head_file",
            "description": (
                "Read the first N lines of a file inside the configured "
                "corpus. Paths outside that directory are refused."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "lines": {"type": "integer", "default": 20},
                },
                "required": ["path"],
            },
        },
    ]
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY unset; running offline corpus search",
            file=sys.stderr,
        )
        return _offline_search(query, corpus_dir)

    client = anthropic.Anthropic()
    messages: list[dict] = [{"role": "user", "content": query}]
    for _turn in range(4):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            tools=tools,
            messages=messages,
        )
        tool_uses = [
            block
            for block in response.content
            if getattr(block, "type", "") == "tool_use"
        ]
        if not tool_uses:
            text = "".join(
                getattr(block, "text", "") for block in response.content
            )
            return text
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in tool_uses:
            payload = block.input if isinstance(block.input, dict) else {}
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": _dispatch_tool(block.name, payload, corpus_dir),
            })
        messages.append({"role": "user", "content": results})
    return "stopped: tool loop reached 4 turns without a final answer"


def main() -> None:
    import tempfile

    root = Path(tempfile.mkdtemp())
    (root / "note.txt").write_text("aisle seat policy\n", encoding="utf-8")
    print(agentic_search_agent("aisle", str(root)))


if __name__ == "__main__":
    main()
