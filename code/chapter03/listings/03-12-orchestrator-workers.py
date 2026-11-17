from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Stub implementations — satisfy type contracts for the pytest gate.
# In production these are replaced by real LLM-backed calls.
# ---------------------------------------------------------------------------

def call_planner(issue: str) -> list[str]:
    """Decompose an open-ended issue into a list of worker tasks."""
    return [f"investigate: {issue}"]


def call_worker(task: str) -> str:
    """Execute a single worker task and return its output."""
    return f"output for: {task}"


def call_compiler(outputs: list[str]) -> str:
    """Synthesize multiple worker outputs into a unified patch or report."""
    return "\n".join(outputs)


# ---------------------------------------------------------------------------
# Orchestrator-workers graph (§3.12 — the dynamic project manager)
# ---------------------------------------------------------------------------

class ReviewState(TypedDict):
    issue: str
    tasks: list[str]
    outputs: list[str]
    patch: str


def plan(state):
    return {"tasks": call_planner(state["issue"])}


def run_workers(state):
    return {"outputs": [call_worker(t) for t in state["tasks"]]}


def synthesize(state):
    return {"patch": call_compiler(state["outputs"])}


g = StateGraph(ReviewState)
g.add_node("plan", plan)
g.add_node("workers", run_workers)
g.add_node("synth", synthesize)
g.add_edge(START, "plan")
g.add_edge("plan", "workers")
g.add_edge("workers", "synth")
g.add_edge("synth", END)
flow = g.compile()


def main() -> None:
    result = flow.invoke({"issue": "login fails"})
    print(result["patch"])


if __name__ == "__main__":
    main()
