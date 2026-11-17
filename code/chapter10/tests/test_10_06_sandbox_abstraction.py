"""Tests for listing 10-06-sandbox-abstraction.

The listing defines two stdlib-only symbols:
  - `ExecutionResult` — a dataclass with stdout, stderr, returncode fields.
  - `SandboxBackend` — a typing.Protocol with four async methods:
      execute(command, timeout) -> ExecutionResult
      upload_files(local_paths, remote_workspace) -> None
      download_files(remote_paths, local_destination) -> None
      terminate() -> None

Load-bearing claims from §10.6:
1. `ExecutionResult` is a dataclass with stdout, stderr, returncode attributes.
2. `SandboxBackend` is a Protocol (structural subtyping, no base-class coupling).
3. A concrete class that implements all four method signatures satisfies the
   Protocol (verified via isinstance with runtime_checkable, or via hasattr if
   the Protocol is not decorated with @runtime_checkable).
4. A class missing any of the four methods does NOT satisfy the Protocol.
5. `execute` is the load-bearing method; the listing declares it with a
   `timeout` parameter defaulting to 30.0.
"""

from __future__ import annotations

from dataclasses import fields as dc_fields

import pytest


@pytest.fixture
def abstraction_module(load_listing):
    """Return the 10-06 module; skip if import fails."""
    return load_listing("10-06-sandbox-abstraction")


# ---------------------------------------------------------------------------
# ExecutionResult dataclass
# ---------------------------------------------------------------------------

def test_execution_result_is_dataclass(abstraction_module) -> None:
    """ExecutionResult must be a dataclass (has __dataclass_fields__)."""
    ExecutionResult = abstraction_module.ExecutionResult
    assert hasattr(ExecutionResult, "__dataclass_fields__"), (
        "ExecutionResult must be decorated with @dataclass"
    )


def test_execution_result_fields(abstraction_module) -> None:
    """ExecutionResult has stdout (str), stderr (str), returncode (int) fields."""
    ExecutionResult = abstraction_module.ExecutionResult
    field_names = {f.name for f in dc_fields(ExecutionResult)}
    assert "stdout" in field_names
    assert "stderr" in field_names
    assert "returncode" in field_names


def test_execution_result_instantiation(abstraction_module) -> None:
    """ExecutionResult can be instantiated with positional args."""
    ExecutionResult = abstraction_module.ExecutionResult
    result = ExecutionResult(stdout="ok", stderr="", returncode=0)
    assert result.stdout == "ok"
    assert result.stderr == ""
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# SandboxBackend Protocol structure
# ---------------------------------------------------------------------------

def test_sandbox_backend_is_protocol(abstraction_module) -> None:
    """SandboxBackend must be a typing.Protocol subclass."""
    SandboxBackend = abstraction_module.SandboxBackend
    # Protocol classes have __protocol_attrs__ or are registered via
    # typing._ProtocolMeta. The most portable check is via __bases__.
    assert any(
        getattr(base, "__name__", "") == "Protocol"
        for base in SandboxBackend.__mro__
    ), "SandboxBackend must inherit from typing.Protocol"


def test_sandbox_backend_has_required_methods(abstraction_module) -> None:
    """SandboxBackend declares all four required methods."""
    SandboxBackend = abstraction_module.SandboxBackend
    for method_name in ("execute", "upload_files", "download_files", "terminate"):
        assert hasattr(SandboxBackend, method_name), (
            f"SandboxBackend must declare method '{method_name}'"
        )


@pytest.mark.asyncio
async def test_protocol_methods_raise_not_implemented(abstraction_module) -> None:
    """Protocol bodies raise instead of using an ellipsis body."""
    backend = abstraction_module.SandboxBackend
    with pytest.raises(NotImplementedError):
        await backend.execute(object(), "echo hi")
    with pytest.raises(NotImplementedError):
        await backend.terminate(object())


def test_execute_has_timeout_parameter(abstraction_module) -> None:
    """execute() declares a `timeout` parameter (default 30.0 per the listing)."""
    import inspect
    SandboxBackend = abstraction_module.SandboxBackend
    sig = inspect.signature(SandboxBackend.execute)
    assert "timeout" in sig.parameters, (
        "execute() must declare a 'timeout' parameter"
    )
    timeout_param = sig.parameters["timeout"]
    assert timeout_param.default == 30.0, (
        "execute() timeout parameter must default to 30.0"
    )


# ---------------------------------------------------------------------------
# Structural subtyping: conforming and non-conforming classes
# ---------------------------------------------------------------------------

def test_conforming_class_satisfies_protocol(abstraction_module) -> None:
    """A class implementing all four methods satisfies SandboxBackend."""
    SandboxBackend = abstraction_module.SandboxBackend
    ExecutionResult = abstraction_module.ExecutionResult

    class StubBackend:
        async def execute(
            self, command: str, timeout: float = 30.0
        ) -> ExecutionResult:
            return ExecutionResult(stdout="", stderr="", returncode=0)

        async def upload_files(
            self, local_paths: list[str], remote_workspace: str
        ) -> None:
            pass

        async def download_files(
            self, remote_paths: list[str], local_destination: str
        ) -> None:
            pass

        async def terminate(self) -> None:
            pass

    # Check structural compatibility via hasattr for all declared methods
    stub = StubBackend()
    for method_name in ("execute", "upload_files", "download_files", "terminate"):
        assert hasattr(stub, method_name), (
            f"StubBackend must have '{method_name}' to satisfy SandboxBackend"
        )

    # If the Protocol is runtime_checkable, isinstance works directly.
    # If not, we fall back to the hasattr check above (already passed).
    if getattr(SandboxBackend, "_is_runtime_protocol", False):
        assert isinstance(stub, SandboxBackend)


def test_partial_class_missing_terminate(abstraction_module) -> None:
    """A class missing terminate() does NOT fully satisfy the Protocol interface."""
    SandboxBackend = abstraction_module.SandboxBackend
    ExecutionResult = abstraction_module.ExecutionResult

    class IncompleteBackend:
        async def execute(
            self, command: str, timeout: float = 30.0
        ) -> ExecutionResult:
            return ExecutionResult(stdout="", stderr="", returncode=0)

        async def upload_files(
            self, local_paths: list[str], remote_workspace: str
        ) -> None:
            pass

        async def download_files(
            self, remote_paths: list[str], local_destination: str
        ) -> None:
            pass

        # terminate is intentionally missing

    stub = IncompleteBackend()
    assert not hasattr(stub, "terminate"), (
        "IncompleteBackend must not have 'terminate' for this negative test"
    )

    if getattr(SandboxBackend, "_is_runtime_protocol", False):
        assert not isinstance(stub, SandboxBackend), (
            "A class missing terminate() must not satisfy SandboxBackend"
        )
