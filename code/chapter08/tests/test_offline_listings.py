"""Offline calls for the chapter 8 listings that touch tools and hooks."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import ClassVar


def test_book_flight_offline_reference(load_listing) -> None:
    module = load_listing("08-03-claude-tool-choice")
    direct = asyncio.run(module.book_flight.handler({"flight_id": "AA100"}))
    assert direct == {
        "booking_reference": "OFFLINE-DEMO",
        "flight_id": "AA100",
    }
    nested = asyncio.run(
        module.book_flight.handler({"args": {"flight_id": "BA9"}})
    )
    assert nested["flight_id"] == "BA9"
    assert module.options.allowed_tools == ["book_flight"]


def test_force_booking_tool_filters_tools(load_listing) -> None:
    module = load_listing("08-03-langchain-tool-choice")

    class _Tool:
        def __init__(self, name: str) -> None:
            self.name = name

    class _Request:
        def __init__(self) -> None:
            self.tools = [_Tool("search_flights"), _Tool("book_flight")]
            self.tool_choice = "auto"

    def handler(request):
        return request

    out = module.force_booking_tool.wrap_model_call(_Request(), handler)
    assert [item.name for item in out.tools] == ["book_flight"]
    assert out.tool_choice == "required"
    assert module.book_flight("AA100")["booking_reference"] == "OFFLINE-DEMO"
    assert module.search_flights("JFK", "LHR") == "offline:JFK:LHR"


def test_policy_options_and_limits(load_listing) -> None:
    claude = load_listing("08-05-claude-policy")
    assert claude.options.max_budget_usd == 50.0
    assert claude.options.disallowed_tools == ["delete_booking"]
    langchain = load_listing("08-05-langchain-policy-middleware")
    assert langchain.model_limit.run_limit == 20
    assert langchain.tool_limit.run_limit == 50
    assert langchain.book_flight("AA100")["flight_id"] == "AA100"


def test_refund_cap_denies_over_limit(load_listing) -> None:
    module = load_listing("08-06-claude-prehook")
    over = SimpleNamespace(
        tool_name="issue_refund", tool_input={"amount": 900}
    )
    denied = asyncio.run(module.enforce_refund_cap(over, "id", None))
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    under = SimpleNamespace(
        tool_name="issue_refund", tool_input={"amount": 10}
    )
    assert asyncio.run(module.enforce_refund_cap(under, "id", None)) == {}


def test_langchain_refund_cap_short_circuits(load_listing) -> None:
    module = load_listing("08-06-langchain-prehook")

    class _Request:
        tool_name = "issue_refund"
        tool_input: ClassVar[dict] = {"amount": 900}

    def handler(_request):
        return {"content": "should not run"}

    out = module.enforce_refund_cap.wrap_tool_call(_Request(), handler)
    assert out["is_error"] is True
    assert "500.00" in out["error"]
    assert module.issue_refund("BK1", 40) == "offline-refund:BK1:40.00"


def test_sanitize_masks_pan_and_ssn(load_listing) -> None:
    module = load_listing("08-07-claude-posthook")
    data = SimpleNamespace(
        tool_response="card 4111111111111111 ssn 123-45-6789"
    )
    out = asyncio.run(module.sanitize_tool_output(data, "id", None))
    text = out["hookSpecificOutput"]["updatedToolOutput"]
    assert "411111××××××1111" in text
    assert "[SSN REDACTED]" in text
    assert "123-45-6789" not in text


def test_langchain_sanitize_output(load_listing) -> None:
    module = load_listing("08-07-langchain-posthook")

    def handler(_request):
        return {"content": "4111111111111111 123-45-6789"}

    out = module.sanitize_output.wrap_tool_call(SimpleNamespace(), handler)
    assert "411111××××××1111" in out["content"]
    assert "[SSN REDACTED]" in out["content"]
    assert module.get_patient_record("p1")["content"] == "offline record"


def test_validation_retry_accepts_on_second_attempt(load_listing) -> None:
    module = load_listing("08-08-validation-retry")

    class _Msg:
        def __init__(self, output: str) -> None:
            self.output = output

    class _Client:
        def __init__(self) -> None:
            self.prompt = ""

        async def query(self, prompt: str, session_id: str = "default"):
            self.prompt = prompt

        async def receive_response(self):
            if "failed validation" in self.prompt:
                yield _Msg("accepted")
            else:
                yield _Msg("rejected")

    def validator(text: object) -> dict:
        if text != "accepted":
            raise ValueError("not accepted")
        return {"status": "accepted"}

    result = asyncio.run(
        module.run_with_validation_retry(_Client(), "book AA100", validator)
    )
    assert result == {"status": "accepted"}


def test_booking_step_accepts_valid_output(load_listing) -> None:
    module = load_listing("08-10-claude-integrated")

    class _Call:
        def __init__(self, output: dict) -> None:
            self.output = output

    class _Msg:
        def __init__(self, calls: list) -> None:
            self.tool_calls = calls

    class _Client:
        async def query(self, prompt: str, session_id: str = "default"):
            return None

        async def receive_response(self):
            yield _Msg(
                [
                    _Call(
                        {
                            "flight_id": "AA100",
                            "passenger_name": "Ada",
                            "price_usd": 200.0,
                        }
                    )
                ]
            )

    assert asyncio.run(module.run_booking_step(_Client(), "book")) is None
    assert module.options.max_budget_usd == 5.0


def test_integrated_stack_blocks_refund_and_masks_pan(load_listing) -> None:
    module = load_listing("08-10-langchain-integrated")

    class _Refund:
        tool_name = "issue_refund"
        tool_input: ClassVar[dict] = {"amount": 900}

    blocked = module.full_validation_stack.wrap_tool_call(
        _Refund(), lambda _request: {"content": "ran"}
    )
    assert blocked["is_error"] is True

    def handler(_request):
        return {"content": "4111111111111111"}

    masked = module.full_validation_stack.wrap_tool_call(
        SimpleNamespace(tool_name="book_flight", tool_input={}),
        handler,
    )
    assert "411111××××××1111" in masked["content"]
    assert module.book_flight("AA100")["booking_reference"] == "OFFLINE-DEMO"
