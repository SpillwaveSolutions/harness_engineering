"""Tests for listing 05-09-context-manager.

Verifies ContextManager budget computation, token footprint estimation,
enforce_result_budget truncation, apply_tool_result_clearing predicate
and count, assemble_final_payload budget guard, persistent-facts prepend,
and the ContextBudgetExceeded exception path.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _make_manager(load_listing, **kwargs):
    """Helper: instantiate ContextManager with a mock client."""
    m = load_listing("05-09-context-manager")
    client = MagicMock()
    return m.ContextManager(client=client, **kwargs), m


def test_budget_equals_int_of_max_tokens_times_utilization(load_listing) -> None:
    """budget == int(max_physical_tokens * target_utilization), default 700000."""
    mgr, _ = _make_manager(load_listing)
    assert mgr.budget == int(1_000_000 * 0.70)
    assert mgr.budget == 700_000


def test_budget_custom_values(load_listing) -> None:
    """budget reflects custom max_physical_tokens and target_utilization."""
    mgr, _ = _make_manager(
        load_listing,
        max_physical_tokens=200_000,
        target_utilization=0.50,
    )
    assert mgr.budget == 100_000


def test_calculate_token_footprint_uses_chars_div_4(load_listing) -> None:
    """calculate_token_footprint returns total_chars // 4."""
    mgr, _ = _make_manager(load_listing)
    messages = [
        {"role": "user", "content": "a" * 400},
        {"role": "assistant", "content": "b" * 400},
    ]
    assert mgr.calculate_token_footprint(messages) == 200


def test_calculate_token_footprint_empty_messages(load_listing) -> None:
    """calculate_token_footprint returns 0 for an empty message list."""
    mgr, _ = _make_manager(load_listing)
    assert mgr.calculate_token_footprint([]) == 0


def test_enforce_result_budget_truncates_long_strings(load_listing) -> None:
    """enforce_result_budget truncates strings over max_tool_result_chars and appends annotation."""
    mgr, _ = _make_manager(load_listing, max_tool_result_chars=100)
    long = "z" * 200
    result = mgr.enforce_result_budget("some_tool", long)
    assert result.startswith("z" * 100)
    assert "trimmed at boundary" in result
    # The raw content before the annotation is exactly max_tool_result_chars chars.
    annotation_start = result.index("\n[trimmed")
    assert annotation_start == 100


def test_enforce_result_budget_returns_short_strings_unchanged(load_listing) -> None:
    """enforce_result_budget returns strings at or below max_tool_result_chars unchanged."""
    mgr, _ = _make_manager(load_listing, max_tool_result_chars=100)
    short = "hello"
    assert mgr.enforce_result_budget("tool", short) == short


def test_enforce_result_budget_returns_non_string_unchanged(load_listing) -> None:
    """enforce_result_budget returns non-string results unchanged."""
    mgr, _ = _make_manager(load_listing)
    for value in [{"key": "val"}, 42, None]:
        assert mgr.enforce_result_budget("tool", value) == value


def _tool_result_message(content_text: str) -> dict:
    """Build a Anthropic-style tool_result message (role=user, type=tool_result)."""
    return {
        "role": "user",
        "content": [{"type": "tool_result", "content": content_text}],
    }


def test_apply_tool_result_clearing_returns_cleared_count(load_listing) -> None:
    """apply_tool_result_clearing clears older tool results and returns count cleared."""
    mgr, _ = _make_manager(load_listing, keep_recent_tool_results=1)
    messages = [
        _tool_result_message("old result 1"),
        _tool_result_message("old result 2"),
        _tool_result_message("recent result"),
    ]
    cleared = mgr.apply_tool_result_clearing(messages)
    assert cleared == 2  # two older ones cleared, one kept


def test_apply_tool_result_clearing_replaces_content_with_placeholder(load_listing) -> None:
    """apply_tool_result_clearing sets cleared messages' content to the placeholder string."""
    mgr, _ = _make_manager(load_listing, keep_recent_tool_results=1)
    messages = [
        _tool_result_message("verbose old result"),
        _tool_result_message("recent"),
    ]
    mgr.apply_tool_result_clearing(messages)
    assert messages[0]["content"] == "[tool result cleared for context budget]"
    # The most recent tool result message is kept intact.
    assert messages[1]["content"] != "[tool result cleared for context budget]"


def test_apply_tool_result_clearing_skips_non_tool_result_messages(load_listing) -> None:
    """apply_tool_result_clearing does not touch regular user or assistant messages."""
    mgr, _ = _make_manager(load_listing, keep_recent_tool_results=0)
    messages = [
        {"role": "user", "content": "plain user message"},
        {"role": "assistant", "content": "assistant reply"},
        _tool_result_message("tool output"),
    ]
    mgr.apply_tool_result_clearing(messages)
    # Only the tool_result message is a candidate; the others stay.
    assert messages[0]["content"] == "plain user message"
    assert messages[1]["content"] == "assistant reply"


def test_apply_tool_result_clearing_returns_zero_when_nothing_to_clear(load_listing) -> None:
    """apply_tool_result_clearing returns 0 when no messages exceed keep_recent."""
    mgr, _ = _make_manager(load_listing, keep_recent_tool_results=5)
    messages = [_tool_result_message("only result")]
    cleared = mgr.apply_tool_result_clearing(messages)
    assert cleared == 0


def test_assemble_final_payload_raises_when_budget_exceeded_and_nothing_clears(
    load_listing,
) -> None:
    """assemble_final_payload raises ContextBudgetExceeded when over budget and nothing can be cleared."""
    m = load_listing("05-09-context-manager")
    client = MagicMock()
    # tiny budget: 10 * 0.70 = 7 tokens
    mgr = m.ContextManager(client=client, max_physical_tokens=10, target_utilization=0.70)
    # No tool_result messages, so clearing returns 0.
    messages = [{"role": "user", "content": "a" * 1000}]
    with pytest.raises(m.ContextBudgetExceeded):
        mgr.assemble_final_payload("system", "", messages)


def test_assemble_final_payload_prepends_persistent_facts(load_listing) -> None:
    """assemble_final_payload prepends persistent_facts to system_prompt."""
    mgr, _ = _make_manager(load_listing)
    system_prompt = "You are a helpful assistant."
    persistent_facts = "PERSISTENT FACTS:\n  order_id: ORD-001"
    messages = [{"role": "user", "content": "hello"}]
    final_system, _ = mgr.assemble_final_payload(system_prompt, persistent_facts, messages)
    assert final_system.startswith(persistent_facts)
    assert system_prompt in final_system


def test_assemble_final_payload_no_facts_uses_system_prompt_verbatim(load_listing) -> None:
    """assemble_final_payload returns system_prompt unchanged when persistent_facts is empty."""
    mgr, _ = _make_manager(load_listing)
    system_prompt = "You are a helpful assistant."
    messages = [{"role": "user", "content": "hello"}]
    final_system, _ = mgr.assemble_final_payload(system_prompt, "", messages)
    assert final_system == system_prompt


def test_assemble_final_payload_triggers_clearing_when_over_budget(load_listing) -> None:
    """assemble_final_payload triggers tool_result clearing when estimated tokens exceed budget."""
    mgr, _ = _make_manager(
        load_listing,
        max_physical_tokens=200,   # budget = 140 tokens
        target_utilization=0.70,
        keep_recent_tool_results=1,  # keep 1 recent; evict older ones
    )
    # Two tool_result messages: one old (will be cleared), one recent (kept).
    # Each list content repr is ~80 chars => ~20 tokens per message => ~40 total, under budget.
    # But we want over-budget before clearing, so use large content.
    messages = [
        _tool_result_message("y" * 2000),  # old: large, will be cleared
        _tool_result_message("recent"),    # recent: kept
    ]
    # Should not raise; clearing the old result brings tokens under budget.
    _final_system, returned_messages = mgr.assemble_final_payload("system", "", messages)
    # The older tool_result content was cleared (replaced with placeholder).
    assert returned_messages[0]["content"] == "[tool result cleared for context budget]"
    # The most recent tool_result is preserved.
    assert returned_messages[1]["content"] != "[tool result cleared for context budget]"


# ---------------------------------------------------------------------------
# OrderedContextAssembler tests
# ---------------------------------------------------------------------------

def _make_assembler(load_listing):
    """Helper: load the listing module and return a fresh OrderedContextAssembler."""
    m = load_listing("05-09-context-manager")
    return m.OrderedContextAssembler(), m


def test_ordered_context_assembler_slot_order_starts_with_system(load_listing) -> None:
    """SLOT_ORDER places 'system' as the first slot."""
    m = load_listing("05-09-context-manager")
    assert m.SLOT_ORDER[0] == "system"


def test_ordered_context_assembler_slot_order_ends_with_user_turn(load_listing) -> None:
    """SLOT_ORDER places 'user_turn' as the last slot."""
    m = load_listing("05-09-context-manager")
    assert m.SLOT_ORDER[-1] == "user_turn"


def test_ordered_context_assembler_slot_order_contains_all_slots(load_listing) -> None:
    """SLOT_ORDER contains all five required slot names."""
    m = load_listing("05-09-context-manager")
    required = {"system", "constraints", "history", "tool_output", "user_turn"}
    assert set(m.SLOT_ORDER) == required


def test_ordered_context_assembler_put_adds_message_to_slot(load_listing) -> None:
    """put() appends a message to the named slot."""
    assembler, _m = _make_assembler(load_listing)
    msg = {"role": "system", "content": "You are a travel booking assistant."}
    assembler.put("system", msg)
    assert assembler.slots["system"].messages == [msg]


def test_ordered_context_assembler_put_multiple_messages_same_slot(load_listing) -> None:
    """put() called twice on the same slot appends both messages in order."""
    assembler, _ = _make_assembler(load_listing)
    msg1 = {"role": "user", "content": "first"}
    msg2 = {"role": "user", "content": "second"}
    assembler.put("user_turn", msg1)
    assembler.put("user_turn", msg2)
    assert assembler.slots["user_turn"].messages == [msg1, msg2]


def test_ordered_context_assembler_assemble_respects_slot_order(load_listing) -> None:
    """assemble() emits messages in SLOT_ORDER, not insertion order."""
    assembler, _m = _make_assembler(load_listing)
    system_msg = {"role": "system", "content": "system prompt"}
    user_msg = {"role": "user", "content": "user turn"}
    history_msg = {"role": "assistant", "content": "prior assistant turn"}
    # Insert in reverse order: user_turn first, then system, then history.
    assembler.put("user_turn", user_msg)
    assembler.put("system", system_msg)
    assembler.put("history", history_msg)
    result = assembler.assemble()
    # Expected order per SLOT_ORDER: system, constraints, history, tool_output, user_turn
    assert result.index(system_msg) < result.index(history_msg)
    assert result.index(history_msg) < result.index(user_msg)


def test_ordered_context_assembler_assemble_system_before_user_turn(load_listing) -> None:
    """assemble() always places system messages before user_turn messages."""
    assembler, _ = _make_assembler(load_listing)
    system_msg = {"role": "system", "content": "pinned facts"}
    user_msg = {"role": "user", "content": "current request"}
    # Put in reverse order to prove ordering is by slot, not insertion.
    assembler.put("user_turn", user_msg)
    assembler.put("system", system_msg)
    result = assembler.assemble()
    assert result[0] == system_msg
    assert result[-1] == user_msg


def test_ordered_context_assembler_assemble_empty_is_empty_list(load_listing) -> None:
    """assemble() with no messages put returns an empty list."""
    assembler, _ = _make_assembler(load_listing)
    assert assembler.assemble() == []


def test_ordered_context_assembler_assemble_flattens_across_slots(load_listing) -> None:
    """assemble() returns all messages from all slots in a single flat list."""
    assembler, _ = _make_assembler(load_listing)
    msgs = {
        "system": {"role": "system", "content": "sys"},
        "constraints": {"role": "user", "content": "constraint"},
        "history": {"role": "assistant", "content": "history"},
        "tool_output": {"role": "user", "content": "tool"},
        "user_turn": {"role": "user", "content": "user"},
    }
    for slot, msg in msgs.items():
        assembler.put(slot, msg)
    result = assembler.assemble()
    assert len(result) == 5
    # All messages present
    for msg in msgs.values():
        assert msg in result


def test_ordered_context_assembler_put_does_not_affect_other_slots(load_listing) -> None:
    """put() on one slot leaves all other slots empty."""
    assembler, m = _make_assembler(load_listing)
    assembler.put("history", {"role": "assistant", "content": "turn 1"})
    for slot_name in m.SLOT_ORDER:
        if slot_name != "history":
            assert assembler.slots[slot_name].messages == []
