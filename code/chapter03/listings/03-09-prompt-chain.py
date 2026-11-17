from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Stub implementations — satisfy type contracts for the pytest gate.
# In production these are replaced by real LLM-backed calls.
# ---------------------------------------------------------------------------

def call_preprocess(raw_document: str) -> str:
    """Normalize whitespace and strip control characters from raw text."""
    return raw_document.strip()


def call_extract(cleaned_text: str) -> dict:
    """Extract key financial fields from cleaned mortgage document text."""
    return {"loan_amount": 0, "interest_rate": 0.0, "term_years": 30}


def call_compliance(extracted_financials: dict) -> str:
    """Run compliance rules against extracted financials, returning a report."""
    return "PASS: all compliance rules satisfied."


# ---------------------------------------------------------------------------
# Prompt-chain graph (§3.9 — the reliable assembly line)
# ---------------------------------------------------------------------------

class MortgageState(TypedDict):
    raw_document: str
    cleaned_text: str
    extracted_financials: dict
    compliance_report: str


def clean(state):
    return {"cleaned_text": call_preprocess(state["raw_document"])}


def extract(state):
    return {"extracted_financials": call_extract(state["cleaned_text"])}


def validate(state):
    return {"compliance_report": call_compliance(state["extracted_financials"])}


g = StateGraph(MortgageState)
g.add_node("clean", clean)
g.add_node("extract", extract)
g.add_node("validate", validate)
g.add_edge(START, "clean")
g.add_edge("clean", "extract")
g.add_edge("extract", "validate")
g.add_edge("validate", END)
chain = g.compile()


def main() -> None:
    result = chain.invoke({"raw_document": "  Borrower: Ada Lovelace  "})
    print(result["cleaned_text"])
    print(result["compliance_report"])


if __name__ == "__main__":
    main()
