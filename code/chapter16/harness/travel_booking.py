"""Stub TravelBookingHarness for chapter 16 listings.

Provides the interface expected by listings 16-01 and 16-08
without requiring the full harness package.  Behavior is
deterministic: the tool-output filter and memory-write validator
from listings 16-02/16-03 are used to actually enforce the
boundaries the test cases exercise.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

from harness.memory import MemorySubsystem

_LISTINGS_DIR = (
    pathlib.Path(__file__).parent.parent / "listings"
)


def _load(slug: str):
    """Load a listing module by slug."""
    path = _LISTINGS_DIR / f"{slug}.py"
    module_name = slug.replace("-", "_")
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@dataclass
class SecurityTestResult:
    blocked: bool
    reached_model: bool
    reason: str = ""


# Injection patterns that the context-length checker rejects
_CTX_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"\bAGENT\b.*?:", re.IGNORECASE),
]

_MAX_CONTEXT_BYTES = 8192


class TravelBookingHarness:
    """Minimal harness used in ch16 security tests.

    Applies listing 16-02 and 16-03 boundary checks; does NOT
    call the Claude API.
    """

    def __init__(
        self,
        memory: MemorySubsystem | None = None,
        model: str = "claude-sonnet-4-6",
        tenant_id: str = "default",
        storage_path: pathlib.Path | None = None,
    ) -> None:
        self.model = model
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self.memory: MemorySubsystem = (
            memory if memory is not None
            else MemorySubsystem(namespace=tenant_id)
        )
        self._injected: dict[str, Any] = {}

    # -----------------------------------------------------------------
    # Interface for listing 16-01
    # -----------------------------------------------------------------

    def inject_tool_response(
        self, tool_name: str, response: Any
    ) -> None:
        """Pre-load a tool response to be used by the next run()."""
        self._injected[tool_name] = response

    def run(self, user_input: str) -> None:
        """Simulate one agent turn using injected tool responses.

        The tool-output filter (listing 16-02) is applied to each
        injected response.  Clean fields are stored in memory.
        Poisoned fields raise ValueError and are dropped.
        """
        filter_mod = _load("16-02-tool-output-filter")
        mem_mod = _load("16-03-memory-write-validator")
        SourceChannel = mem_mod.SourceChannel

        for tool_name, raw_response in self._injected.items():
            if tool_name == "search_flights" and isinstance(
                raw_response, dict
            ):
                try:
                    typed = filter_mod.filter_search_flights_output(
                        raw_response
                    )
                    # Write clean fields to memory as tool output
                    clean_content = (
                        f"airline={typed.airline} "
                        f"origin={typed.origin} "
                        f"destination={typed.destination}"
                    )
                    try:
                        mem_mod.validate_memory_write(
                            clean_content,
                            self.tenant_id,
                            "session-run",
                            SourceChannel.TOOL_OUTPUT,
                        )
                        self.memory.write(clean_content)
                    except ValueError:
                        pass  # Validator blocked the content
                except (TypeError, AttributeError, RuntimeError):
                    pass

        self._injected.clear()

    # -----------------------------------------------------------------
    # Interface for listing 16-08
    # -----------------------------------------------------------------

    def run_security_test(self, case: Any) -> SecurityTestResult:
        """Run a single InjectionTestCase and report the result.

        Dispatches to the appropriate boundary check based on
        case.boundary value.
        """

        boundary = case.boundary.value
        payload = case.attack_payload

        if boundary == "context":
            return self._test_context_boundary(payload)
        elif boundary == "tool":
            return self._test_tool_boundary(payload)
        elif boundary == "memory":
            return self._test_memory_boundary(payload)
        else:
            return SecurityTestResult(
                blocked=False,
                reached_model=True,
                reason=f"unknown boundary: {boundary}",
            )

    def _test_context_boundary(
        self, payload: dict
    ) -> SecurityTestResult:
        user_input: str = payload.get("user_input", "")
        # Check length gate
        if len(user_input.encode("utf-8")) > _MAX_CONTEXT_BYTES:
            return SecurityTestResult(
                blocked=True,
                reached_model=False,
                reason="context length exceeded",
            )
        # Check injection patterns
        for pat in _CTX_PATTERNS:
            if pat.search(user_input):
                return SecurityTestResult(
                    blocked=True,
                    reached_model=False,
                    reason=f"injection pattern: {pat.pattern}",
                )
        return SecurityTestResult(
            blocked=False, reached_model=True
        )

    def _test_tool_boundary(
        self, payload: dict
    ) -> SecurityTestResult:
        response: dict = payload.get("response", {})
        filter_mod = _load("16-02-tool-output-filter")
        try:
            filtered = filter_mod.filter_search_flights_output(
                response
            )
        except (ValueError, TypeError, AttributeError) as exc:
            # Filter raised: injection detected and blocked
            return SecurityTestResult(
                blocked=True,
                reached_model=False,
                reason=str(exc),
            )
        # Structural exclusion check: scan the raw response for
        # injection patterns in fields that do NOT appear in the
        # typed FlightSearchResult (e.g. vendor_notes).  If such
        # content is present in raw but absent from the filtered
        # output, the structural filter blocked it.
        import json as _json
        raw_text = _json.dumps(response)
        filtered_text = filtered.model_dump_json()
        for pat in _CTX_PATTERNS:
            if pat.search(raw_text) and not pat.search(
                filtered_text
            ):
                return SecurityTestResult(
                    blocked=True,
                    reached_model=False,
                    reason=(
                        "structural exclusion: injection in "
                        f"unschema'd field, pattern={pat.pattern}"
                    ),
                )
        # Also check for HTML comment patterns in raw vs filtered
        _html_comment = re.compile(r"<!--.*?-->", re.DOTALL)
        if _html_comment.search(raw_text) and not (
            _html_comment.search(filtered_text)
        ):
            return SecurityTestResult(
                blocked=True,
                reached_model=False,
                reason=(
                    "structural exclusion: HTML comment in "
                    "unschema'd field dropped by typed filter"
                ),
            )
        return SecurityTestResult(
            blocked=False, reached_model=True
        )

    def _test_memory_boundary(
        self, payload: dict
    ) -> SecurityTestResult:
        content: str = payload.get("content", "")
        source: str = payload.get("source", "tool_output")
        mem_mod = _load("16-03-memory-write-validator")
        SourceChannel = mem_mod.SourceChannel
        channel_map = {
            "user_input": SourceChannel.USER_INPUT,
            "tool_output": SourceChannel.TOOL_OUTPUT,
            "model_inference": SourceChannel.MODEL_INFERENCE,
        }
        channel = channel_map.get(
            source, SourceChannel.TOOL_OUTPUT
        )
        try:
            mem_mod.validate_memory_write(
                content, self.tenant_id, "session-test", channel
            )
            return SecurityTestResult(
                blocked=False, reached_model=True
            )
        except ValueError as exc:
            return SecurityTestResult(
                blocked=True,
                reached_model=False,
                reason=str(exc),
            )
