"""Tests for listing 06-04-memory-directory.

Verifies file-backed cross-session memory: session_start_load,
session_end_write (with provenance header), list_memory_keys, key
overwrite, and per-user isolation. Pure stdlib, no API key required.
Tests monkeypatch the module's MEMORY_ROOT so each test runs against a
fresh tmp directory.
"""

from __future__ import annotations


def test_session_start_load_returns_empty_when_no_directory(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    assert m.session_start_load("alice") == {}


def test_session_end_write_creates_user_dir_and_provenance_header(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    path = m.session_end_write("alice", "preferences", "vegetarian, no fish")
    assert path.exists()
    content = path.read_text()
    assert "vegetarian, no fish" in content
    assert content.startswith("<!-- updated:")


def test_session_start_load_returns_files_after_writes(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    m.session_end_write("alice", "preferences", "vegetarian, no fish")
    m.session_end_write("alice", "allergies", "penicillin (severe)")
    loaded = m.session_start_load("alice")
    assert set(loaded.keys()) == {"preferences", "allergies"}
    assert "vegetarian" in loaded["preferences"]
    assert "penicillin" in loaded["allergies"]


def test_session_end_write_overwrites_existing_key(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    m.session_end_write("alice", "preferences", "vegetarian")
    m.session_end_write("alice", "preferences", "vegan")
    loaded = m.session_start_load("alice")
    assert "vegan" in loaded["preferences"]
    assert "vegetarian" not in loaded["preferences"].replace("vegan", "")


def test_list_memory_keys_returns_empty_for_no_user(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    assert m.list_memory_keys("alice") == []


def test_list_memory_keys_after_writes(
    load_listing, tmp_path, monkeypatch
) -> None:
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    m.session_end_write("alice", "preferences", "x")
    m.session_end_write("alice", "allergies", "y")
    assert sorted(m.list_memory_keys("alice")) == ["allergies", "preferences"]


def test_per_user_isolation(load_listing, tmp_path, monkeypatch) -> None:
    """Different user_ids have isolated memory directories."""
    m = load_listing("06-04-memory-directory")
    monkeypatch.setattr(m, "MEMORY_ROOT", tmp_path / "agent_memory")
    m.session_end_write("alice", "preferences", "alice-pref")
    m.session_end_write("bob", "preferences", "bob-pref")
    alice = m.session_start_load("alice")
    bob = m.session_start_load("bob")
    assert "alice-pref" in alice["preferences"]
    assert "bob-pref" in bob["preferences"]
    assert "alice-pref" not in bob.get("preferences", "")
    assert "bob-pref" not in alice.get("preferences", "")


# ---------------------------------------------------------------------------
# Adversarial path-traversal tests (§6.4 / §6.7 memory-as-attack-surface).
# Regression coverage for the _safe_user_dir() sanitizer added in this
# chapter's security pass: an attacker-supplied user_id MUST collapse to
# an alphanumeric+'-_' subset and never escape MEMORY_ROOT.
# ---------------------------------------------------------------------------


def _assert_under_root(written: object, root: object) -> None:
    """Resolved write path must be a descendant of MEMORY_ROOT."""
    from pathlib import Path
    written_real = Path(str(written)).resolve()
    root_real = Path(str(root)).resolve()
    assert root_real in written_real.parents, (
        f"path escape: {written_real} is not under {root_real}"
    )


def test_path_traversal_double_dot_blocked(
    load_listing, tmp_path, monkeypatch
) -> None:
    """A '../../etc' user_id sanitizes to 'etc' under MEMORY_ROOT."""
    m = load_listing("06-04-memory-directory")
    root = tmp_path / "agent_memory"
    monkeypatch.setattr(m, "MEMORY_ROOT", root)

    written = m.session_end_write("../../etc", "preferences", "pwned")
    _assert_under_root(written, root)
    # Sanitizer drops '.' and '/', collapses '../../etc' -> 'etc'.
    assert written.parent.name == "etc"
    # No file was created at /etc/preferences.md (the attack target).
    from pathlib import Path
    assert not Path("/etc/preferences.md").exists()


def test_path_traversal_backslash_blocked(
    load_listing, tmp_path, monkeypatch
) -> None:
    """A '..\\..\\windows' user_id sanitizes to 'windows' under MEMORY_ROOT."""
    m = load_listing("06-04-memory-directory")
    root = tmp_path / "agent_memory"
    monkeypatch.setattr(m, "MEMORY_ROOT", root)

    written = m.session_end_write("..\\..\\windows", "preferences", "pwned")
    _assert_under_root(written, root)
    # Sanitizer drops '.' and '\\', collapses '..\\..\\windows' -> 'windows'.
    assert written.parent.name == "windows"


def test_unsafe_chars_collapse_to_safe_subset(
    load_listing, tmp_path, monkeypatch
) -> None:
    """Mixed traversal + shell metacharacters collapse to alnum + '-_' only."""
    m = load_listing("06-04-memory-directory")
    root = tmp_path / "agent_memory"
    monkeypatch.setattr(m, "MEMORY_ROOT", root)

    # alice/../../bob;rm -rf  -> alicebobrm-rf  (drops / . ; space)
    written = m.session_end_write(
        "alice/../../bob;rm -rf", "preferences", "pwned"
    )
    _assert_under_root(written, root)
    assert written.parent.name == "alicebobrm-rf"
    # And reads/lists target the same sanitized namespace.
    assert m.list_memory_keys("alice/../../bob;rm -rf") == ["preferences"]
    loaded = m.session_start_load("alice/../../bob;rm -rf")
    assert "pwned" in loaded["preferences"]
