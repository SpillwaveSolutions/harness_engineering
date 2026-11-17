"""Offline stand-in for the agent SDK hook protocol used by listing 14-10.

AgentHooks subclasses override pre_tool_use and post_tool_use.
HookResult.allow() permits the call. HookResult.block(reason=...) stops it.
This file does not import or call the agent SDK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HookResult:
    """Result object returned from hook methods."""

    allowed: bool
    reason: str = ""

    @classmethod
    def allow(cls) -> HookResult:
        """Permit the pending tool call to proceed."""
        return cls(allowed=True)

    @classmethod
    def block(cls, reason: str = "") -> HookResult:
        """Prevent the pending tool call; surface *reason* to the harness."""
        return cls(allowed=False, reason=reason)


class AgentHooks:
    """
    Base class for harness lifecycle hooks.

    Subclass and override the methods you need; unoverridden methods
    default to allow().
    """

    def pre_tool_use(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> HookResult:
        """Called before every tool invocation. Default: allow."""
        return HookResult.allow()

    def post_tool_use(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
    ) -> HookResult:
        """Called after every tool invocation. Default: allow."""
        return HookResult.allow()
