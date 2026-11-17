"""Tests for listing 11-06-approval-gate.

The listing defines `ApprovalRequest` and the async
`request_human_approval` coroutine. `notify_fn` and `poll_fn` are
abstract callables in the prose; the test injects minimal stubs to
exercise the four decision branches.

Load-bearing claims from §11.6:
1. `notify_fn` is awaited exactly once when the approval flow starts.
2. The polling loop exits as soon as `poll_fn` returns a decision.
3. The returned decision is the value supplied by `poll_fn["choice"]`.
4. Timeout + irreversible=True yields ("deny", <audit rationale>).
5. Timeout + irreversible=False yields ("allow", <audit rationale>).
6. The function returns a 2-tuple `(decision, rationale)` where
   `decision in {"allow", "deny"}` — never "timeout".
"""

from __future__ import annotations

import pytest


@pytest.fixture
def approval_module(load_listing):
    return load_listing("11-06-approval-gate")


@pytest.fixture
def sample_request(approval_module):
    return approval_module.ApprovalRequest(
        session_id="sess_test_001",
        tool_name="book_flight",
        tool_input={"fare_id": "abc"},
        critic_objection="business class violates economy ceiling",
        confidence_score=0.12,
        requested_at=0.0,
    )


async def test_notify_is_called_once_on_entry(
    approval_module, sample_request,
):
    notify_calls: list = []

    async def notify_fn(req):
        notify_calls.append(req)

    async def poll_fn(session_id):
        return {"choice": "allow", "rationale": "ok"}

    await approval_module.request_human_approval(
        sample_request,
        notify_fn=notify_fn,
        poll_fn=poll_fn,
        irreversible=True,
    )
    assert len(notify_calls) == 1
    assert notify_calls[0] is sample_request


async def test_human_allow_decision_returns_allow(
    approval_module, sample_request,
):
    async def notify_fn(req):
        pass

    async def poll_fn(session_id):
        return {"choice": "allow", "rationale": "approved by Sarah"}

    decision, rationale = await approval_module.request_human_approval(
        sample_request,
        notify_fn=notify_fn,
        poll_fn=poll_fn,
        irreversible=True,
    )
    assert decision == "allow"
    assert rationale == "approved by Sarah"


async def test_human_deny_decision_returns_deny(
    approval_module, sample_request,
):
    async def notify_fn(req):
        pass

    async def poll_fn(session_id):
        return {"choice": "deny", "rationale": "policy violation"}

    decision, rationale = await approval_module.request_human_approval(
        sample_request,
        notify_fn=notify_fn,
        poll_fn=poll_fn,
        irreversible=True,
    )
    assert decision == "deny"
    assert rationale == "policy violation"


async def test_irreversible_timeout_defaults_to_deny(
    approval_module, sample_request, monkeypatch,
):
    # Force timeout immediately by setting the window to zero seconds.
    monkeypatch.setattr(
        approval_module, "APPROVAL_TIMEOUT_SECONDS", 0,
    )

    async def notify_fn(req):
        pass

    async def poll_fn(session_id):
        return None  # never returns a decision

    decision, rationale = await approval_module.request_human_approval(
        sample_request,
        notify_fn=notify_fn,
        poll_fn=poll_fn,
        irreversible=True,
    )
    assert decision == "deny"
    assert rationale is not None
    assert "irreversible" in rationale.lower()


async def test_reversible_timeout_defaults_to_allow(
    approval_module, sample_request, monkeypatch,
):
    monkeypatch.setattr(
        approval_module, "APPROVAL_TIMEOUT_SECONDS", 0,
    )

    async def notify_fn(req):
        pass

    async def poll_fn(session_id):
        return None

    decision, rationale = await approval_module.request_human_approval(
        sample_request,
        notify_fn=notify_fn,
        poll_fn=poll_fn,
        irreversible=False,
    )
    assert decision == "allow"
    assert rationale is not None
    assert "audit" in rationale.lower()


async def test_decision_is_never_timeout_string(
    approval_module, sample_request, monkeypatch,
):
    """Regression: the prose docstring previously claimed decision could
    be 'timeout', but the implementation only returns 'allow' or 'deny'
    (the timeout branch maps to one of those). This pins the contract."""
    monkeypatch.setattr(
        approval_module, "APPROVAL_TIMEOUT_SECONDS", 0,
    )

    async def notify_fn(req):
        pass

    async def poll_fn(session_id):
        return None

    for irreversible in (True, False):
        decision, _ = await approval_module.request_human_approval(
            sample_request,
            notify_fn=notify_fn,
            poll_fn=poll_fn,
            irreversible=irreversible,
        )
        assert decision in {"allow", "deny"}
        assert decision != "timeout"


def test_approval_request_carries_audit_fields(approval_module):
    req = approval_module.ApprovalRequest(
        session_id="sess_x",
        tool_name="book_flight",
        tool_input={"k": "v"},
        critic_objection="o",
        confidence_score=0.1,
        requested_at=1.0,
    )
    assert req.session_id == "sess_x"
    assert req.tool_name == "book_flight"
    assert req.confidence_score == 0.1


def test_default_timeout_is_five_minutes(approval_module):
    assert approval_module.APPROVAL_TIMEOUT_SECONDS == 300
