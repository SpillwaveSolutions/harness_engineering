"""Tests for listing 12-15-harness-integration.

Depends on a2a-sdk (A2AClient, A2ACardResolver, AgentCard, etc.) and
anthropic. Skips gracefully if either is not installed.

Structural claims from §12.15:
- The listing exports a dataclass `BookingContext` with fields:
  session_id, a2a_task_ids (dict), artifacts (dict).
- The listing exports a class `TravelBookingHarness` with a
  `LOYALTY_AGENT_URL` class attribute and async methods:
  `book_travel`, `_discover_loyalty_agent`, `_delegate_loyalty_check`.
"""

from __future__ import annotations


def test_listing_loads(load_listing):
    module = load_listing("12-15-harness-integration")
    assert module is not None


def test_travel_booking_harness_class_exists(load_listing):
    module = load_listing("12-15-harness-integration")
    assert hasattr(module, "TravelBookingHarness")


def test_booking_context_class_exists(load_listing):
    module = load_listing("12-15-harness-integration")
    assert hasattr(module, "BookingContext")


def test_loyalty_agent_url_is_defined(load_listing):
    module = load_listing("12-15-harness-integration")
    harness_cls = module.TravelBookingHarness
    assert hasattr(harness_cls, "LOYALTY_AGENT_URL")
    assert "loyalty" in harness_cls.LOYALTY_AGENT_URL.lower()


async def test_book_travel_offline(load_listing, monkeypatch):
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    module = load_listing("12-15-harness-integration")
    harness = module.TravelBookingHarness()
    result = await harness.book_travel("book a hotel", "ACC123456")
    assert result["loyalty"]["status"] == "offline"
    assert result["loyalty"]["accountId"] == "ACC123456"
    assert result["tasks"]["loyalty"] == "offline-loyalty"
    assert result["flights"]["options"] == []


async def test_input_required_is_raised(load_listing, monkeypatch):
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    module = load_listing("12-15-harness-integration")

    from a2a.types import (
        Message,
        Part,
        Role,
        StreamResponse,
        TaskStatus,
        TaskStatusUpdateEvent,
    )

    event = StreamResponse(
        status_update=TaskStatusUpdateEvent(
            task_id="task-1",
            status=TaskStatus(
                state=module.TaskState.TASK_STATE_INPUT_REQUIRED,
                message=Message(
                    message_id="q",
                    role=Role.ROLE_AGENT,
                    parts=[Part(text="which dates?")],
                ),
            ),
        )
    )

    async def events(message):
        del message
        yield event

    monkeypatch.setattr(module, "_open_stream", events)
    harness = module.TravelBookingHarness()
    ctx = module.BookingContext(session_id="booking-test")
    card = module._local_loyalty_card()
    try:
        await harness._delegate_loyalty_check(ctx, "ACC1", card)
    except module.InputRequired as exc:
        assert "which dates?" in str(exc)
    else:
        raise AssertionError("input-required must raise InputRequired")


def test_main_prints_card_refusal_and_exits(load_listing, monkeypatch, capsys):
    module = load_listing("12-15-harness-integration")

    async def refuse(self, *_args, **_kwargs):
        raise module.CardResolutionError(
            "Refusing an unverified loyalty card."
        )

    monkeypatch.setattr(
        module.TravelBookingHarness, "book_travel", refuse
    )
    assert module.main() == 1
    captured = capsys.readouterr()
    assert "unverified" in captured.err.lower()
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out


async def test_offline_card_is_labelled_stand_in(load_listing, monkeypatch):
    """Without the live flag the card is the labelled stand-in."""
    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    module = load_listing("12-15-harness-integration")
    card = await module.TravelBookingHarness()._discover_loyalty_agent()
    assert "OFFLINE STAND-IN" in card.description


async def test_live_card_failure_refuses_unverified_card(
    load_listing, monkeypatch
):
    """A failed live resolution does not fall back to the stand-in card."""
    monkeypatch.setenv("HARNESS_LIVE_API", "1")
    module = load_listing("12-15-harness-integration")

    class BrokenResolver:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        async def get_agent_card(self):
            raise module.AgentCardResolutionError("no signed card")

    monkeypatch.setattr(module, "A2ACardResolver", BrokenResolver)
    harness = module.TravelBookingHarness()
    try:
        await harness._discover_loyalty_agent()
    except module.CardResolutionError as exc:
        assert "unverified" in str(exc).lower()
    else:
        raise AssertionError("live failure must refuse the card")
    assert harness._loyalty_card is None
