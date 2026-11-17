"""Tests for 09-07-schema-driven-tool: verifies Optional import removed.

Per action_item index 5 in evals/runs/2026-06-13T19:36:12Z-ch09/verdict.json:
'Remove unused Optional import from from typing import Literal, Optional.'

CodeTestPlan:
- Test that the listing module loads without error.
- Test that `Optional` is NOT imported (the fix).
- Test that `Literal` IS still imported (regression guard).
- Test that BookFlightInput validates correct inputs and rejects invalid ones.
- Test that BOOK_FLIGHT_TOOL has the required three keys (name, description,
  input_schema).
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from pydantic import ValidationError

LISTING_PATH = (
    pathlib.Path(__file__).parent.parent / "listings" / "09-07-schema-driven-tool.py"
)


def _parse_imports(source: str) -> set[str]:
    """Return the set of names imported from `typing` in the source."""
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            for alias in node.names:
                imported.add(alias.name)
    return imported


def test_optional_not_in_typing_imports() -> None:
    """Optional must be absent from the typing import line after the fix."""
    source = LISTING_PATH.read_text()
    typing_imports = _parse_imports(source)
    assert "Optional" not in typing_imports, (
        "Optional should have been removed from the typing import; "
        "it was unused and the verdict action_item requires its removal."
    )


def test_literal_still_in_typing_imports() -> None:
    """Literal must still be imported -- it is used for cabin_class."""
    source = LISTING_PATH.read_text()
    typing_imports = _parse_imports(source)
    assert "Literal" in typing_imports, (
        "Literal is used in BookFlightInput.cabin_class and must remain imported."
    )


def test_listing_loads(load_listing) -> None:
    """The listing must load without raising an ImportError or SyntaxError."""
    module = load_listing("09-07-schema-driven-tool")
    public = [n for n in dir(module) if not n.startswith("_")]
    assert public, "listing loaded but exposes no public names"


def test_book_flight_tool_structure(load_listing) -> None:
    """BOOK_FLIGHT_TOOL must have name, description, and input_schema keys."""
    module = load_listing("09-07-schema-driven-tool")
    tool = module.BOOK_FLIGHT_TOOL
    assert "name" in tool, "BOOK_FLIGHT_TOOL missing 'name'"
    assert "description" in tool, "BOOK_FLIGHT_TOOL missing 'description'"
    assert "input_schema" in tool, "BOOK_FLIGHT_TOOL missing 'input_schema'"
    assert tool["name"] == "book_flight"


def test_book_flight_input_valid(load_listing) -> None:
    """BookFlightInput accepts a valid payload."""
    module = load_listing("09-07-schema-driven-tool")
    BookFlightInput = module.BookFlightInput
    obj = BookFlightInput(origin="JFK", destination="LHR", date="2026-09-15")
    assert obj.origin == "JFK"
    assert obj.destination == "LHR"
    assert obj.cabin_class == "economy"  # default


def test_book_flight_input_invalid_iata(load_listing) -> None:
    """BookFlightInput rejects a non-IATA origin code."""
    module = load_listing("09-07-schema-driven-tool")
    BookFlightInput = module.BookFlightInput
    with pytest.raises(ValidationError):
        BookFlightInput(origin="jfk", destination="LHR", date="2026-09-15")


def test_write_audit_entry_appends_local_record(load_listing) -> None:
    module = load_listing("09-07-schema-driven-tool")
    module.write_audit_entry(
        session_id="sess",
        tool_name="book_flight",
        caller_identity="agent",
        input_validated={"origin": "JFK"},
        result_type="success",
        latency_ms=12.5,
    )
    entry = module._AUDIT_LOG[-1]
    assert entry["session_id"] == "sess"
    assert entry["tool_name"] == "book_flight"
    assert entry["result_type"] == "success"
    assert entry["caller_identity"] == "agent"


def test_book_flight_input_invalid_date(load_listing) -> None:
    """BookFlightInput rejects a malformed date string."""
    module = load_listing("09-07-schema-driven-tool")
    BookFlightInput = module.BookFlightInput
    with pytest.raises(ValidationError):
        BookFlightInput(origin="JFK", destination="LHR", date="09/15/2026")
