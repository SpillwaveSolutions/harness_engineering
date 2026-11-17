"""pytest conftest for chapter 13.

Provides a `load_listing` fixture that imports a listing by its NN-MM-slug id.
Listings have hyphens in filenames (per the NN-MM-slug naming convention), so
they cannot be imported with normal `import` syntax — we go through
`importlib.util.spec_from_file_location`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent / "listings"


@pytest.fixture
def load_listing():
    """Return a callable that loads a listing by its id (e.g. '13-01-otel-model-span')."""

    def _load(listing_id: str) -> ModuleType:
        path = LISTINGS_DIR / f"{listing_id}.py"
        if not path.exists():
            pytest.fail(f"listing {listing_id} not found at {path}")
        spec = importlib.util.spec_from_file_location(
            listing_id.replace("-", "_"), path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    return _load
