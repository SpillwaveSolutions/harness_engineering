"""Tests for listing 10-02-worktree-lifecycle.

The listing defines `run_agent_in_worktree`, an async function that:
  ① Creates an isolated git worktree via subprocess.run(["git", "worktree", "add", ...])
  ② Runs agent work in that worktree (calls `invoke_agent`, a prose-only symbol)
  ③ Gates on pytest before returning success
  ④ Force-removes the worktree on exception via subprocess.run(["git", "worktree",
     "remove", "--force", ...])

Because `invoke_agent` is a prose-only symbol (not defined in the listing),
the module-level import succeeds but calling `run_agent_in_worktree` would
fail unless we monkeypatch it. We test the subprocess orchestration logic by
patching both `subprocess.run` and `invoke_agent` at module scope.

Tests:
1. Smoke: module imports cleanly or skips (no syntax errors, stdlib-only deps).
2. Success path: worktree add called, test gate called, success dict returned.
3. Failure path: exception inside agent work triggers force-remove and re-raises.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_module_imports(load_listing) -> None:
    """Module loads cleanly and exposes the worktree runner."""
    module = load_listing("10-02-worktree-lifecycle")
    assert callable(module.run_agent_in_worktree)
    assert callable(module.invoke_agent)


@pytest.mark.asyncio
async def test_invoke_agent_returns_offline_status(load_listing) -> None:
    module = load_listing("10-02-worktree-lifecycle")
    result = await module.invoke_agent("book flight", cwd="/tmp/unused")
    assert result == {"status": "ok", "task": "book flight"}


@pytest.mark.asyncio
async def test_success_path_creates_and_returns_ok(load_listing) -> None:
    """On success: worktree add fires, tests pass, ok dict returned."""
    module = load_listing("10-02-worktree-lifecycle")

    # inject invoke_agent into the module so the call doesn't NameError
    mock_invoke = AsyncMock(return_value={"output": "booked"})
    module.invoke_agent = mock_invoke

    # subprocess.run is called twice: worktree add (check=True), then pytest
    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        return result

    with patch.object(module.subprocess, "run", side_effect=fake_run) as mock_run:
        outcome = await module.run_agent_in_worktree(
            "book flight",
            base_branch="main",
            worktree_base=Path("/tmp/test-worktrees"),
        )

    assert outcome["status"] == "ok"
    assert "branch" in outcome
    assert "worktree" in outcome

    # First call must include "worktree" and "add"
    first_call_cmd = mock_run.call_args_list[0][0][0]
    assert "worktree" in first_call_cmd
    assert "add" in first_call_cmd


@pytest.mark.asyncio
async def test_test_failure_returns_test_failed(load_listing) -> None:
    """When the pytest subprocess returns non-zero, status is test_failed."""
    module = load_listing("10-02-worktree-lifecycle")

    mock_invoke = AsyncMock(return_value={"output": "booked"})
    module.invoke_agent = mock_invoke

    call_count = [0]

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        call_count[0] += 1
        # First call is worktree add (check=True, succeeds); second is pytest (fails)
        if call_count[0] == 1:
            result.returncode = 0
        else:
            result.returncode = 1
        return result

    with patch.object(module.subprocess, "run", side_effect=fake_run):
        outcome = await module.run_agent_in_worktree(
            "book flight",
            base_branch="main",
            worktree_base=Path("/tmp/test-worktrees"),
        )

    assert outcome["status"] == "test_failed"
    assert "branch" in outcome


@pytest.mark.asyncio
async def test_exception_triggers_force_remove(load_listing) -> None:
    """An exception in agent work causes git worktree remove --force and re-raises."""
    module = load_listing("10-02-worktree-lifecycle")

    # invoke_agent raises to simulate agent failure
    mock_invoke = AsyncMock(side_effect=RuntimeError("agent exploded"))
    module.invoke_agent = mock_invoke

    force_remove_called = []

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        if "--force" in cmd:
            force_remove_called.append(cmd)
        return result

    with (
        patch.object(module.subprocess, "run", side_effect=fake_run),
        pytest.raises(RuntimeError, match="agent exploded"),
    ):
            await module.run_agent_in_worktree(
                "book flight",
                base_branch="main",
                worktree_base=Path("/tmp/test-worktrees"),
            )

    assert force_remove_called, (
        "git worktree remove --force must be called when agent raises"
    )
    assert any("remove" in " ".join(cmd) for cmd in force_remove_called)
