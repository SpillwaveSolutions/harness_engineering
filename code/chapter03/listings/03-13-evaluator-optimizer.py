from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Stub implementations — satisfy type contracts for the pytest gate.
# In production these are replaced by real LLM-backed calls.
# ---------------------------------------------------------------------------

def call_generator(prompt: str, critique: str | None = None) -> str:
    """Generate a draft response, optionally incorporating a critique."""
    if critique:
        return f"revised draft addressing: {critique}"
    return f"initial draft for: {prompt}"


def call_evaluator(draft: str) -> tuple[int, str]:
    """Score a draft (0-100) and return a (score, critique) tuple."""
    score = 95 if draft.startswith("revised") else 70
    critique = "" if score >= 90 else "draft needs improvement"
    return score, critique


# ---------------------------------------------------------------------------
# EvalState TypedDict — the shared state passed between graph nodes (§3.13)
# ---------------------------------------------------------------------------

class EvalState(TypedDict):
    prompt: str
    draft: str
    passed: bool
    critique: str
    iteration: int


# ---------------------------------------------------------------------------
# Node functions for the evaluator-optimizer cycle (§3.13)
# ---------------------------------------------------------------------------

def generator(state: EvalState) -> dict:
    """Generate or revise a draft, reading the previous critique as context.

    ① Refinement is a context-engineering act: the critique travels as part of
    the generator's input on every pass after the first.
    """
    return {
        "draft": call_generator(state["prompt"], state.get("critique")),
        "iteration": state.get("iteration", 0) + 1,
    }


def evaluator(state: EvalState) -> dict:
    """Score the current draft and decide whether the loop continues.

    ② The evaluator returns both a binary ``passed`` flag and the linguistic
    critique: the binary gates the loop, the critique steers the next draft.
    """
    score, critique = call_evaluator(state["draft"])
    return {"passed": score >= 90, "critique": critique}


# ---------------------------------------------------------------------------
# Conditional edge — route back to generator or exit (§3.13)
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 3


def route_after_eval(state: EvalState) -> str:
    """Return 'generator' to loop, or END to exit.

    ③ A hard ``max_iterations`` bound (3 in this book's pipeline) prevents
    runaway token bills if the loop fails to converge.
    """
    if state["passed"] or state.get("iteration", 0) >= MAX_ITERATIONS:
        return END
    return "generator"


# ---------------------------------------------------------------------------
# LangGraph cycle wiring — EvalState + StateGraph + conditional looping edge
# ---------------------------------------------------------------------------

g = StateGraph(EvalState)
g.add_node("generator", generator)
g.add_node("evaluator", evaluator)
g.add_edge(START, "generator")
g.add_edge("generator", "evaluator")
g.add_conditional_edges("evaluator", route_after_eval)
graph = g.compile()


def main() -> None:
    result = graph.invoke(
        {
            "prompt": "Summarize harness patterns.",
            "draft": "",
            "passed": False,
            "critique": None,
            "iteration": 0,
        }
    )
    print(result["passed"])
    print(result["iteration"])
    print(result["draft"])


if __name__ == "__main__":
    main()
