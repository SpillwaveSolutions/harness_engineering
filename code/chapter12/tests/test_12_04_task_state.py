"""Tests for listing 12-04-task-state.

The listing re-exports the eight a2a.types.TaskState constants the
harness branches on.
"""

from __future__ import annotations

from a2a.types import TaskState


def test_eight_sdk_constants(load_listing):
    module = load_listing("12-04-task-state")
    values = {
        module.SUBMITTED,
        module.WORKING,
        module.INPUT_REQUIRED,
        module.AUTH_REQUIRED,
        module.COMPLETED,
        module.CANCELED,
        module.FAILED,
        module.REJECTED,
    }
    assert values == {
        TaskState.TASK_STATE_SUBMITTED,
        TaskState.TASK_STATE_WORKING,
        TaskState.TASK_STATE_INPUT_REQUIRED,
        TaskState.TASK_STATE_AUTH_REQUIRED,
        TaskState.TASK_STATE_COMPLETED,
        TaskState.TASK_STATE_CANCELED,
        TaskState.TASK_STATE_FAILED,
        TaskState.TASK_STATE_REJECTED,
    }
    assert len(values) == 8
