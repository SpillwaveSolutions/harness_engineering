import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _parse_skill_frontmatter(skill_path: str) -> dict[str, Any]:
    """Read the YAML-like block between the first two --- lines."""
    text = Path(skill_path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"no frontmatter in {skill_path}")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"frontmatter not closed in {skill_path}")
    data: dict[str, Any] = {}
    key: str | None = None
    mode: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal key, mode, buf
        if key is None:
            return
        if mode == "list":
            data[key] = buf
        elif mode == "fold":
            data[key] = " ".join(
                part.strip() for part in buf if part.strip()
            )
        buf = []
        key = None
        mode = None

    for raw in text[3:end].splitlines():
        if raw.startswith("  - ") and mode == "list":
            buf.append(raw[4:].strip())
            continue
        if raw.startswith(" ") and mode == "fold":
            buf.append(raw.strip())
            continue
        if ":" not in raw:
            continue
        flush()
        name, _, value = raw.partition(":")
        key = name.strip()
        value = value.strip()
        if value in {">", "|"}:
            mode = "fold"
            buf = []
        elif value == "":
            mode = "list"
            buf = []
        else:
            data[key] = value.strip('"')
            key = None
    flush()
    return data


@dataclass
class CapabilityRegistry:
    """Holds tools and skills with shared discovery, permissions, audit."""

    _tools: dict[str, dict] = field(default_factory=dict)
    _skills: dict[str, dict] = field(default_factory=dict)
    _allowed_tools: set[str] = field(default_factory=set)
    _audit_log: list[dict] = field(default_factory=list)

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable[..., Any],
        allowed_callers: list[str] | None = None,
    ) -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": handler,
            "allowed_callers": allowed_callers or [],
        }
        self._allowed_tools.add(name)

    def register_skill(self, skill_path: str) -> None:
        """Parse SKILL.md frontmatter and index for discovery."""
        frontmatter = _parse_skill_frontmatter(skill_path)   # not shown
        self._skills[frontmatter["name"]] = {
            "path": skill_path,
            "name": frontmatter["name"],
            "description": frontmatter["description"],
            "allowed_tools": frontmatter.get("allowed-tools", []),
            "context": frontmatter.get("context", "default"),
        }

    def tool_definitions(self) -> list[dict]:
        """Returns tool definitions for the Claude API tools= parameter."""
        return [
            {"name": t["name"], "description": t["description"],
             "input_schema": t["input_schema"]}
            for t in self._tools.values()
        ]

    def dispatch_tool(
        self,
        tool_name: str,
        tool_input: dict,
        session_id: str,
        caller: str,
    ) -> dict:
        start = time.monotonic()
        if tool_name not in self._tools:
            self._write_audit(session_id, tool_name, caller,
                              "denied", time.monotonic() - start)
            return {"error": "Tool not found", "is_retryable": False}

        tool = self._tools[tool_name]
        if tool["allowed_callers"] and caller not in tool["allowed_callers"]:
            self._write_audit(session_id, tool_name, caller,
                              "permission_denied", time.monotonic() - start)
            return {"error": "Permission denied", "is_retryable": False}

        result = tool["handler"](**tool_input)
        self._write_audit(session_id, tool_name, caller,
                          "success", time.monotonic() - start)
        return result

    def _write_audit(
        self, session_id: str, tool_name: str,
        caller: str, result_type: str, latency: float,
    ) -> None:
        self._audit_log.append({
            "audit_id": str(uuid.uuid4()),
            "session_id": session_id,
            "tool_name": tool_name,
            "caller": caller,
            "result_type": result_type,
            "latency_ms": round(latency * 1000, 2),
            "timestamp": time.time(),
        })


def main() -> None:
    registry = CapabilityRegistry()
    skill = Path(__file__).with_name("09-11-skill-md.txt")
    registry.register_skill(str(skill))
    print(min(registry._skills))


if __name__ == "__main__":
    main()
