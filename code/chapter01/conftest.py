"""pytest conftest for chapter 1.

Loads a listing by its NN-MM-slug id. Filenames contain hyphens, so
import goes through importlib. A missing file or a failed import
raises; nothing here is skipped.
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
    """Load a listing module by id, for example '01-01-search-cap'."""

    def _load(listing_id: str) -> ModuleType:
        path = LISTINGS_DIR / f"{listing_id}.py"
        if not path.is_file():
            raise FileNotFoundError(path)
        spec = importlib.util.spec_from_file_location(
            listing_id.replace("-", "_"),
            path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    return _load
