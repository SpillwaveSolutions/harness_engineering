"""Mask card numbers and SSNs after a tool returns."""

from __future__ import annotations

import re

from deepagents import create_deep_agent
from langchain.agents.middleware import wrap_tool_call

PAN_PATTERN = re.compile(r"\b(\d{6})\d{6,9}(\d{4})\b")
SSN_PATTERN = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")


def get_patient_record(patient_id: str) -> dict:
    """Return a local record. No network."""
    return {"patient_id": patient_id, "content": "offline record"}


def book_appointment(patient_id: str, when: str) -> dict:
    """Book an appointment. No network."""
    return {
        "patient_id": patient_id,
        "when": when,
        "status": "booked",
    }


@wrap_tool_call
def sanitize_output(request, handler):
    result = handler(request)
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        content = PAN_PATTERN.sub(r"\1××××××\2", content)
        content = SSN_PATTERN.sub("[SSN REDACTED]", content)
        result = {**result, "content": content}
    return result


agent = create_deep_agent(
    model="claude-sonnet-4-6",
    tools=[get_patient_record, book_appointment],
    system_prompt="Redact identifiers in tool output.",
    middleware=[sanitize_output],
)


def main() -> None:
    print(get_patient_record("p1")["content"])


if __name__ == "__main__":
    main()
