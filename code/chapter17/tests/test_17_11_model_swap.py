"""Tests for listing 17-11-model-swap.

Verifies that the listing is syntactically valid, has an async
rehearse_model_swap function, an if __name__ == '__main__' guard,
uses asyncio.run() in that guard, does not have an unused import
asyncio, and fits within 75-char line width.
"""

from __future__ import annotations

import ast
import pathlib
import sys

import pytest

_CHAPTER_ROOT = pathlib.Path(__file__).parent.parent
_LISTING_PATH = _CHAPTER_ROOT / "listings" / "17-11-model-swap.py"


def _source() -> str:
    return _LISTING_PATH.read_text()


def _tree() -> ast.Module:
    return ast.parse(_source())


def test_listing_file_exists():
    """Listing file must be present on disk."""
    assert _LISTING_PATH.exists(), f"Missing: {_LISTING_PATH}"


def test_listing_is_valid_python():
    """Listing must parse as valid Python 3.13 syntax."""
    try:
        ast.parse(_source())
    except SyntaxError as exc:
        pytest.fail(f"SyntaxError in listing: {exc}")


def test_rehearse_model_swap_is_async_function():
    """rehearse_model_swap must be defined as an async def."""
    tree = _tree()
    async_funcs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
    ]
    assert "rehearse_model_swap" in async_funcs, (
        "Expected async def rehearse_model_swap() in listing"
    )


def test_main_guard_present():
    """Listing must have an if __name__ == '__main__' guard."""
    source = _source()
    assert '__name__ == "__main__"' in source or (
        "__name__ == '__main__'" in source
    ), "Missing if __name__ == '__main__' guard"


def test_asyncio_run_in_main_guard():
    """asyncio.run() must be called inside the __main__ guard."""
    source = _source()
    assert "asyncio.run(" in source, (
        "asyncio.run() not found; entry-point guard must call it"
    )


def test_asyncio_imported():
    """asyncio must be imported (used by the __main__ guard)."""
    source = _source()
    assert "import asyncio" in source, (
        "asyncio not imported but asyncio.run() is required"
    )


def test_production_model_constant_defined():
    """PRODUCTION_MODEL constant must be present."""
    source = _source()
    assert "PRODUCTION_MODEL" in source


def test_candidate_model_constant_defined():
    """CANDIDATE_MODEL constant must be present."""
    source = _source()
    assert "CANDIDATE_MODEL" in source


def test_rehearse_model_swap_offline(monkeypatch):
    """rehearse_model_swap returns a deterministic verdict without a live model."""
    import asyncio
    import importlib.util

    monkeypatch.delenv("HARNESS_LIVE_API", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spec = importlib.util.spec_from_file_location(
        "listing_17_11_exec", _LISTING_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    verdict = asyncio.run(mod.rehearse_model_swap())
    assert verdict["pass"] is False
    assert verdict["status"] == "skipped"
    assert verdict["reason"] == "no evals run"


def test_missing_eval_files_are_not_a_pass(tmp_path, monkeypatch):
    """A missing eval set and baseline must not print a promotion PASS."""
    import asyncio
    import importlib.util

    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "listing_17_11_missing", _LISTING_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    verdict = asyncio.run(mod.rehearse_model_swap())
    assert verdict["pass"] is False
    assert "no evals run" in verdict["reason"]
    code = mod.main()
    assert code != 0


def test_listing_script_exits_nonzero_without_evals():
    """python listings/17-11-model-swap.py exits non-zero when nothing ran."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(_LISTING_PATH)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, proc.stdout
    assert "SKIPPED:" in proc.stdout
    assert "PASS:" not in proc.stdout
    assert "Traceback" not in proc.stderr


def test_no_line_exceeds_75_chars():
    """All lines in the listing file must be within 75 characters."""
    lines = _source().splitlines()
    violations = [
        (i + 1, len(line), line)
        for i, line in enumerate(lines)
        if len(line) > 75
    ]
    assert violations == [], (
        "Lines exceeding 75 chars:\n"
        + "\n".join(
            f"  line {n} ({length} chars): {text}"
            for n, length, text in violations
        )
    )
