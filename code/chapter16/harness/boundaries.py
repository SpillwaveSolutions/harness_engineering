"""Stub boundary helpers for chapter 16 listings.

Provides the interface expected by listing 16-06 by delegating
to the already-extracted listing modules:
  - filter_tool_output  -> listing 16-02
  - validate_memory_write -> listing 16-03
  - verify_agent_card   -> listing 16-05
  - SourceChannel       -> listing 16-03

enforce_context_length is a simple byte-truncation helper
implemented here directly.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Any

_LISTINGS_DIR = (
    pathlib.Path(__file__).parent.parent / "listings"
)


def _load(slug: str):
    """Load a listing module by slug without importing it globally."""
    path = _LISTINGS_DIR / f"{slug}.py"
    module_name = slug.replace("-", "_")
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# Re-export SourceChannel from listing 16-03
_mem_mod = _load("16-03-memory-write-validator")
SourceChannel = _mem_mod.SourceChannel
validate_memory_write = _mem_mod.validate_memory_write

# Re-export verify_agent_card from listing 16-05
_jws_mod = _load("16-05-jws-agent-card-sign-verify")
verify_agent_card = _jws_mod.verify_agent_card


def enforce_context_length(
    text: str, max_bytes: int = 8192
) -> str:
    """Truncate text so its UTF-8 encoding does not exceed max_bytes."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def filter_tool_output(tool_name: str, raw_output: Any) -> Any:
    """Route tool output through the appropriate typed filter.

    Only search_flights has a custom filter; other tools pass
    through unchanged.
    """
    if tool_name == "search_flights" and isinstance(raw_output, dict):
        _filter_mod = _load("16-02-tool-output-filter")
        return _filter_mod.filter_search_flights_output(raw_output)
    return raw_output
