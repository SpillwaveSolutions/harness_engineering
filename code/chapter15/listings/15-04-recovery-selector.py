from enum import Enum


class RecoveryAction(Enum):
    RESUME = "resume"
    BRANCH = "branch"
    ABANDON = "abandon"

def select_recovery(
    error_type: str,
    budget_exhausted: bool,
    checkpoint_corrupt: bool,
    is_debugging: bool,
) -> RecoveryAction:
    if checkpoint_corrupt or budget_exhausted:    # ①
        return RecoveryAction.ABANDON
    if is_debugging:                              # ②
        return RecoveryAction.BRANCH
    transient = {"timeout", "rate_limit", "network", "restart"}
    if error_type in transient:                   # ③
        return RecoveryAction.RESUME
    return RecoveryAction.ABANDON                 # ④
