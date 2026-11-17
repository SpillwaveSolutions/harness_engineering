"""Tests for listing 14-09-gate-script (§14.12).

Verifies:
  - Module imports without NameError (parse_args, load_json, run_eval_sweep
    all defined).
  - main() guard present.
  - load_json reads a real temp JSON file correctly.
  - run_eval_sweep returns the four expected lane keys.
  - Module has an `if __name__ == "__main__": main()` guard.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

LISTINGS_DIR = pathlib.Path(__file__).parent.parent / "listings"


def _load_module():
    """Load 14-09 with 14-07 available (sibling listing)."""
    path = LISTINGS_DIR / "14-09-gate-script.py"
    spec = importlib.util.spec_from_file_location(
        "listing_14_09", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["listing_14_09"] = mod
    spec.loader.exec_module(mod)    # type: ignore[union-attr]
    return mod


def test_module_imports_without_nameerror():
    """§14.12: parse_args, load_json, run_eval_sweep must be defined."""
    mod = _load_module()
    assert callable(getattr(mod, "parse_args", None))
    assert callable(getattr(mod, "load_json", None))
    assert callable(getattr(mod, "run_eval_sweep", None))
    assert callable(getattr(mod, "main", None))


def test_load_json_reads_temp_file():
    """§14.12: load_json must parse a real JSON file correctly."""
    mod = _load_module()
    data = {"quality": {"booking_quality": 0.90}}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(data, f)
        tmppath = f.name
    result = mod.load_json(tmppath)
    assert result == data


def test_run_eval_sweep_returns_four_lanes():
    """§14.12: run_eval_sweep must return quality, safety, cost, policy keys."""
    mod = _load_module()
    data = {
        "quality": {"booking_quality": 0.90},
        "safety": {"no_prompt_injection": True},
        "cost": {"cost_usd_per_session": 0.30},
        "policy": {"gdpr_compliant": True},
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(data, f)
        tmppath = f.name
    result = mod.run_eval_sweep(tmppath)
    for lane in ("quality", "safety", "cost", "policy"):
        assert lane in result, (
            f"run_eval_sweep must return '{lane}' key"
        )


def test_main_missing_args_exits_2():
    """Running the script with no arguments exits 2 and prints usage."""
    script = LISTINGS_DIR / "14-09-gate-script.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "usage" in proc.stderr.lower()
    assert "Traceback" not in proc.stderr
    assert "IndexError" not in proc.stderr


def test_main_with_explicit_args(tmp_path):
    """main() accepts explicit arguments and exits 0 when every lane passes."""
    mod = _load_module()
    baseline = tmp_path / "baseline.json"
    dataset = tmp_path / "eval.json"
    baseline.write_text(json.dumps({"booking_quality": 0.90}))
    dataset.write_text(json.dumps({
        "quality": {"booking_quality": 0.90},
        "safety": {"no_prompt_injection": True},
        "cost": {"cost_usd_per_session": 0.30},
        "policy": {"gdpr_compliant": True},
    }))
    with pytest.raises(SystemExit) as exc:
        mod.main([
            "--baseline-scores",
            str(baseline),
            "--eval-dataset",
            str(dataset),
        ])
    assert exc.value.code == 0


def test_main_guard_present():
    """§14.12: listing must contain if __name__ == '__main__' guard."""
    path = LISTINGS_DIR / "14-09-gate-script.py"
    source = path.read_text()
    assert '__name__ == "__main__"' in source or (
        "__name__ == '__main__'" in source
    ), "listing must have if __name__ == '__main__': main() guard"
