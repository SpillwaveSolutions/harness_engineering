"""Tests for listing 07-10-agentic-search."""

from __future__ import annotations

import pathlib


def test_head_file_returns_first_n_lines(
    tmp_path: pathlib.Path, load_listing
) -> None:
    module = load_listing("07-10-agentic-search")
    corpus_file = tmp_path / "doc.txt"
    corpus_file.write_text("\n".join(f"line {i}" for i in range(1, 11)))
    result = module.head_file(str(corpus_file), lines=3, corpus_dir=str(tmp_path))
    assert result.strip().splitlines() == ["line 1", "line 2", "line 3"]


def test_grep_corpus_finds_matching_files(
    tmp_path: pathlib.Path, load_listing
) -> None:
    module = load_listing("07-10-agentic-search")
    match_file = tmp_path / "match.txt"
    match_file.write_text("RICO racketeering charges\n")
    other_file = tmp_path / "other.txt"
    other_file.write_text("Standard securities filing\n")
    result = module.grep_corpus("RICO", str(tmp_path))
    assert str(match_file.resolve()) in result
    assert str(other_file.resolve()) not in result


def test_grep_treats_leading_dash_as_data(
    tmp_path: pathlib.Path, load_listing
) -> None:
    module = load_listing("07-10-agentic-search")
    secret = tmp_path / "secret.txt"
    secret.write_text("token -n value\n")
    result = module.grep_corpus("-n", str(tmp_path))
    assert str(secret.resolve()) in result


def test_head_file_rejects_paths_outside_corpus(
    tmp_path: pathlib.Path, load_listing
) -> None:
    module = load_listing("07-10-agentic-search")
    outside = tmp_path.parent / "ch7-outside.txt"
    outside.write_text("secret\n")
    try:
        assert (
            module.head_file(str(outside), lines=1, corpus_dir=str(tmp_path))
            == ""
        )
        link = tmp_path / "link.txt"
        link.symlink_to(outside)
        assert (
            module.head_file(str(link), lines=1, corpus_dir=str(tmp_path))
            == ""
        )
    finally:
        outside.unlink(missing_ok=True)


def test_agentic_search_offline_reads_corpus(
    tmp_path: pathlib.Path, load_listing, monkeypatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("07-10-agentic-search")
    (tmp_path / "a.txt").write_text("aisle seat policy\n")
    text = module.agentic_search_agent("aisle", str(tmp_path))
    assert "aisle seat policy" in text


def test_head_file_rejects_non_int_lines(
    tmp_path: pathlib.Path, load_listing
) -> None:
    module = load_listing("07-10-agentic-search")
    corpus_file = tmp_path / "doc.txt"
    corpus_file.write_text("line 1\n")
    try:
        module.head_file(str(corpus_file), lines="3", corpus_dir=str(tmp_path))
    except TypeError as exc:
        assert "lines must be an int" in str(exc)
    else:
        raise AssertionError("a non-int line count must raise TypeError")
    message = module._dispatch_tool(
        "head_file",
        {"path": str(corpus_file), "lines": "3"},
        str(tmp_path),
    )
    assert "lines must be an int" in message


def test_commands_are_not_a_shell(load_listing) -> None:
    module = load_listing("07-10-agentic-search")
    source = pathlib.Path(module.__file__).read_text()
    assert "shell=True" not in source
    assert '"--"' in source
