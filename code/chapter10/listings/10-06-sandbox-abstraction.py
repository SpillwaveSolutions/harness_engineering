from dataclasses import dataclass
from typing import Protocol


@dataclass  # ①
class ExecutionResult:
    stdout: str
    stderr: str
    returncode: int

class SandboxBackend(Protocol):  # ②
    """One interface; three implementations behind it."""

    async def execute(  # ③
        self,
        command: str,
        timeout: float = 30.0,
    ) -> ExecutionResult:
        raise NotImplementedError

    async def upload_files(
        self,
        local_paths: list[str],
        remote_workspace: str,
    ) -> None:
        raise NotImplementedError

    async def download_files(
        self,
        remote_paths: list[str],
        local_destination: str,
    ) -> None:
        raise NotImplementedError

    async def terminate(self) -> None:  # ④
        raise NotImplementedError


def main() -> int:
    sample = ExecutionResult(stdout="", stderr="", returncode=0)
    print(
        f"stdout={sample.stdout!r} stderr={sample.stderr!r} "
        f"returncode={sample.returncode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
