from datetime import UTC, datetime
from pathlib import Path

MEMORY_ROOT = Path("./agent_memory")


def _safe_user_dir(user_id: str) -> Path:
    """Sanitize user_id to prevent path traversal: alnum + '-' + '_' only.

    An attacker-supplied user_id like '../../etc' or '..\\..\\windows' collapses
    to 'etc' or 'windows' under MEMORY_ROOT, never escaping it. This is the
    memory-as-attack-surface boundary defense covered in §6.7.
    """
    safe_id = "".join(c for c in user_id if c.isalnum() or c in "-_")
    return MEMORY_ROOT / safe_id


def session_start_load(user_id: str) -> dict:
    """Load persistent memory at the start of a session."""
    user_dir = _safe_user_dir(user_id)
    memory = {}
    if user_dir.exists():
        for f in user_dir.glob("*.md"):
            memory[f.stem] = f.read_text()  # ① load all memory files into dict
    return memory

def session_end_write(user_id: str, key: str, content: str) -> Path:
    """Write or update a memory file at session end."""
    user_dir = _safe_user_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    target = user_dir / f"{key}.md"
    # ② keep a simple provenance header in every file
    header = f"<!-- updated: {datetime.now(UTC).isoformat()} -->\n"
    target.write_text(header + content)
    return target

def list_memory_keys(user_id: str) -> list[str]:
    """Return all memory file names for a user: the directory IS the index."""
    user_dir = _safe_user_dir(user_id)
    if not user_dir.exists():
        return []
    return [f.stem for f in user_dir.glob("*.md")]  # ③ no database query needed


def main() -> None:
    import tempfile

    global MEMORY_ROOT
    MEMORY_ROOT = Path(tempfile.mkdtemp()) / "agent_memory"
    session_end_write("demo", "preferences", "aisle seat")
    loaded = session_start_load("demo")
    print(loaded["preferences"].splitlines()[-1])
    print(list_memory_keys("demo"))


if __name__ == "__main__":
    main()
