"""Tests for listing 03-09-prompt-chain (§3.9).

Validates the prompt-chain pipeline (the reliable assembly line):
- The three stub call_* functions satisfy their type contracts.
- The compiled LangGraph chain accepts a raw_document and returns a
  compliance_report without raising.

"""

from __future__ import annotations


def test_call_preprocess_returns_string(load_listing):
    """§3.9: call_preprocess must return a str given a str input."""
    listing = load_listing("03-09-prompt-chain")

    result = listing.call_preprocess("  raw mortgage text  ")

    assert isinstance(result, str)
    assert result  # non-empty


def test_call_extract_returns_dict(load_listing):
    """§3.9: call_extract must return a dict given cleaned text."""
    listing = load_listing("03-09-prompt-chain")

    result = listing.call_extract("cleaned mortgage text")

    assert isinstance(result, dict)


def test_call_compliance_returns_string(load_listing):
    """§3.9: call_compliance must return a str given a dict of financials."""
    listing = load_listing("03-09-prompt-chain")

    result = listing.call_compliance({"loan_amount": 100_000})

    assert isinstance(result, str)
    assert result  # non-empty


def test_chain_runs_end_to_end(load_listing):
    """§3.9: the compiled StateGraph chain must process a raw_document
    and produce a non-empty compliance_report without raising."""
    listing = load_listing("03-09-prompt-chain")

    result = listing.chain.invoke({"raw_document": "Borrower: Ada Lovelace"})

    assert "compliance_report" in result
    assert isinstance(result["compliance_report"], str)
    assert result["compliance_report"]


def test_chain_preserves_raw_document(load_listing):
    """§3.9: intermediate state fields are populated after the chain runs."""
    listing = load_listing("03-09-prompt-chain")

    result = listing.chain.invoke({"raw_document": "Loan amount: $500,000"})

    assert "cleaned_text" in result
    assert "extracted_financials" in result
    assert isinstance(result["extracted_financials"], dict)
