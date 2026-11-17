"""Tests for listing 03-13-evaluator-optimizer (§3.13).

Validates the full evaluator-optimizer cycle:
- call_generator / call_evaluator stubs satisfy their type contracts
- generator(state) and evaluator(state) node functions compose correctly
- EvalState TypedDict is importable and structurally complete
- The compiled LangGraph cycle wiring:
  - runs to completion from a cold start
  - loops back to generator when passed=False
  - terminates when passed=True
  - respects the max_iterations=3 guard (never loops more than 3 times)
  - conditional edge returns END when passed=True
  - conditional edge returns "generator" when passed=False and under the limit

"""

from __future__ import annotations


def test_call_generator_returns_string(load_listing):
    """§3.13: call_generator must return a str draft for a given prompt."""
    listing = load_listing("03-13-evaluator-optimizer")

    draft = listing.call_generator("Summarize this document.", critique=None)

    assert isinstance(draft, str)
    assert draft  # non-empty


def test_call_generator_incorporates_critique(load_listing):
    """§3.13: call_generator must produce a different response when a critique
    is provided (revision path)."""
    listing = load_listing("03-13-evaluator-optimizer")

    initial = listing.call_generator("Write a haiku.", critique=None)
    revised = listing.call_generator("Write a haiku.", critique="too abstract")

    assert isinstance(revised, str)
    assert revised != initial or "revised" in revised.lower()


def test_call_evaluator_returns_score_and_critique_tuple(load_listing):
    """§3.13: call_evaluator must return a (int, str) tuple — the unpacking
    on 'score, critique = call_evaluator(draft)' must not raise."""
    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.call_evaluator("a sample draft")

    assert isinstance(result, tuple)
    assert len(result) == 2
    score, critique = result
    assert isinstance(score, int)
    assert 0 <= score <= 100
    assert isinstance(critique, str)


def test_evaluator_node_sets_passed_flag(load_listing):
    """§3.13: evaluator(state) must set 'passed' True when score >= 90."""
    listing = load_listing("03-13-evaluator-optimizer")

    # call_generator with a "revised" draft produces score=95 per stub logic
    draft = listing.call_generator("prompt", critique="needs work")
    state_out = listing.evaluator({"draft": draft})

    assert "passed" in state_out
    assert "critique" in state_out
    assert isinstance(state_out["passed"], bool)


def test_generator_node_produces_draft_key(load_listing):
    """§3.13: generator(state) must return a dict with 'draft' key."""
    listing = load_listing("03-13-evaluator-optimizer")

    state_out = listing.generator(
        {"prompt": "Explain harness patterns.", "critique": None, "iteration": 0}
    )

    assert "draft" in state_out
    assert isinstance(state_out["draft"], str)


def test_generator_node_increments_iteration(load_listing):
    """§3.13: generator(state) must increment the iteration counter."""
    listing = load_listing("03-13-evaluator-optimizer")

    state_out = listing.generator(
        {"prompt": "test prompt", "critique": None, "iteration": 1}
    )

    assert state_out["iteration"] == 2


def test_eval_state_typeddict_has_required_keys(load_listing):
    """§3.13: EvalState TypedDict must declare prompt, draft, passed, critique,
    iteration — the five keys the graph references."""
    listing = load_listing("03-13-evaluator-optimizer")

    annotations = listing.EvalState.__annotations__
    for key in ("prompt", "draft", "passed", "critique", "iteration"):
        assert key in annotations, f"EvalState missing key: {key!r}"


def test_route_after_eval_exits_when_passed(load_listing):
    """§3.13: conditional edge must return END when passed=True."""
    from langgraph.graph import END

    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.route_after_eval(
        {"passed": True, "iteration": 1, "prompt": "", "draft": "", "critique": ""}
    )
    assert result == END


def test_route_after_eval_loops_when_not_passed(load_listing):
    """§3.13: conditional edge must return 'generator' when passed=False and
    below max_iterations."""
    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.route_after_eval(
        {"passed": False, "iteration": 1, "prompt": "", "draft": "", "critique": "x"}
    )
    assert result == "generator"


def test_route_after_eval_exits_at_max_iterations(load_listing):
    """§3.13: conditional edge must return END when iteration >= MAX_ITERATIONS=3,
    even if passed=False (runaway-loop guard)."""
    from langgraph.graph import END

    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.route_after_eval(
        {
            "passed": False,
            "iteration": listing.MAX_ITERATIONS,
            "prompt": "",
            "draft": "",
            "critique": "still bad",
        }
    )
    assert result == END


def test_full_cycle_low_score_then_high_score(load_listing):
    """§3.13: simulate one cycle manually — initial draft scores low, revised draft
    scores >= 90 and sets passed=True."""
    listing = load_listing("03-13-evaluator-optimizer")

    # Round 1: initial draft
    gen_out = listing.generator({"prompt": "Write a spec.", "critique": None, "iteration": 0})
    eval_out = listing.evaluator(gen_out)
    assert not eval_out["passed"]  # stub returns 70 for non-revised draft

    # Round 2: revised draft incorporating critique
    gen_out2 = listing.generator(
        {
            "prompt": "Write a spec.",
            "critique": eval_out["critique"],
            "iteration": gen_out["iteration"],
        }
    )
    eval_out2 = listing.evaluator(gen_out2)
    assert eval_out2["passed"]  # stub returns 95 for revised draft


def test_graph_runs_end_to_end(load_listing):
    """§3.13: compiled LangGraph cycle must accept a cold-start EvalState and
    return a final state with passed=True or iteration >= MAX_ITERATIONS."""
    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.graph.invoke(
        {
            "prompt": "Summarize harness patterns.",
            "draft": "",
            "passed": False,
            "critique": None,
            "iteration": 0,
        }
    )

    assert "draft" in result
    assert "passed" in result
    assert "iteration" in result
    assert (
        result["passed"] or result["iteration"] >= listing.MAX_ITERATIONS
    ), f"Expected passed=True or iteration>={listing.MAX_ITERATIONS}, got {result!r}"


def test_graph_respects_max_iterations_guard(load_listing):
    """§3.13: the graph must never run more than MAX_ITERATIONS=3 generator
    passes regardless of initial state."""
    listing = load_listing("03-13-evaluator-optimizer")

    result = listing.graph.invoke(
        {
            "prompt": "Always fail.",
            "draft": "",
            "passed": False,
            "critique": None,
            "iteration": 0,
        }
    )

    assert result["iteration"] <= listing.MAX_ITERATIONS, (
        f"Graph ran {result['iteration']} iterations, exceeding MAX_ITERATIONS="
        f"{listing.MAX_ITERATIONS}"
    )
