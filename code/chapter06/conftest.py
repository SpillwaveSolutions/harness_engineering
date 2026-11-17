"""pytest conftest for chapter 6.

Load a listing by its NN-MM-slug id. Filenames contain hyphens, so
importlib loads them from listings/. Import failures propagate.
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
    """Return a callable that loads a listing by id."""

    def _load(listing_id: str) -> ModuleType:
        path = LISTINGS_DIR / f"{listing_id}.py"
        if not path.exists():
            raise FileNotFoundError(
                f"listing {listing_id} is not at {path}"
            )
        spec = importlib.util.spec_from_file_location(
            listing_id.replace("-", "_"), path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load listing {listing_id}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    return _load
