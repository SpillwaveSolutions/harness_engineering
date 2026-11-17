import asyncio
import json
import subprocess
from pathlib import Path


async def invoke_agent(task: str, cwd: str) -> dict:
    """Offline stand-in for the agent that runs inside a worktree."""
    del cwd
    return {"status": "ok", "task": task}


async def run_agent_in_worktree(
    task: str,
    base_branch: str = "main",
    worktree_base: Path = Path("../worktrees"),
) -> dict:
    """Spin up a worktree, run the agent, return status."""
    branch = f"agent/{task.replace(' ', '-')[:40]}"
    worktree_path = worktree_base / branch.replace("/", "-")

    # ① Create the isolated worktree
    subprocess.run(  # noqa: ASYNC221
        ["git", "worktree", "add", "-b", branch,
         str(worktree_path), base_branch],
        check=True,
    )
    try:
        # ② Agent work happens here, completely isolated from main checkout
        result = await invoke_agent(task, cwd=str(worktree_path))

        # ③ Gate on tests before merge
        test_result = subprocess.run(  # noqa: ASYNC221
            ["python", "-m", "pytest", "--tb=short", "-q"],
            cwd=str(worktree_path),
            capture_output=True,
            check=False,
        )
        if test_result.returncode != 0:
            return {"status": "test_failed", "branch": branch}

        return {
            "status": "ok",
            "branch": branch,
            "worktree": str(worktree_path),
            "agent": result,
        }
    except Exception:
        # ④ Discard worktree on failure (no residue in main repo)
        subprocess.run(  # noqa: ASYNC221
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            check=False,
        )
        raise


def main() -> int:
    result = asyncio.run(invoke_agent("book a flight", cwd="."))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
