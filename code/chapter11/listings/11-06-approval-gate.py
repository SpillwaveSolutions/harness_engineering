import asyncio
import time
from dataclasses import dataclass

APPROVAL_TIMEOUT_SECONDS = 300  # 5 minutes for irreversible actions

@dataclass
class ApprovalRequest:
    session_id: str
    tool_name: str
    tool_input: dict
    critic_objection: str
    confidence_score: float
    requested_at: float

async def request_human_approval(
    approval_request: ApprovalRequest,
    notify_fn,  # sends Slack/email notification
    poll_fn,    # checks approval store for decision
    irreversible: bool,
) -> tuple[str, str | None]:
    """Returns (decision, rationale). decision is 'allow' | 'deny'."""
    # ① fire external notification; never blocks a thread
    await notify_fn(approval_request)
    deadline = time.monotonic() + APPROVAL_TIMEOUT_SECONDS

    # ② poll until decision arrives or deadline passes
    while time.monotonic() < deadline:
        decision = await poll_fn(approval_request.session_id)
        if decision is not None:
            return decision["choice"], decision.get("rationale")
        await asyncio.sleep(5)

    # ③ Timeout: policy encoded in the branch, not the approval form
    # ④ reversibility axis from §11.5
    if irreversible:
        rationale = (
            "Approval timeout -- irreversible action aborted "
            "(default-deny)"
        )
        return "deny", rationale
    else:
        rationale = (
            "Approval timeout -- reversible action proceeded "
            "with audit entry"
        )
        return "allow", rationale
