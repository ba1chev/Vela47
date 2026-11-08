import pathlib
from typing import Iterator

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxCommandResult


class SandboxEnvLocal(SandboxEnv):
    """A plain directory on the host, with no containment beyond path confinement.

    Files written here are real files, which is enough to build and test every tool
    without a container runtime. What it deliberately cannot do is run commands: a
    subagent asking to execute code it just authored is the ordinary case, and
    honouring that on the host would mean running model-written code with the
    server's own privileges. run() therefore refuses rather than degrading quietly,
    so the absence of a sandbox surfaces as a clear message to the agent instead of
    as an unnoticed security hole.

    It also backs the Docker environment's file operations: the files stay on the host
    and are read and written here, without a round trip through the daemon, while a
    container only ever sees a copy of them made for one command."""

    MAX_FILE_BYTES = 200_000
    SKIPPED_DIRECTORIES = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}

    def __init__(self, root: pathlib.Path, identifier: str = "local") -> None:
        self._root: pathlib.Path = pathlib.Path(root).resolve()
        self._root.mkdir(parents = True, exist_ok = True)
        self._identifier: str = identifier

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def root(self) -> pathlib.Path:
        return self._root

    def resolve(self, relative_path: str) -> pathlib.Path:
        candidate = (self._root / relative_path).resolve()

        if not candidate.is_relative_to(self._root):
            raise ValueError(
                f"Path '{relative_path}' resolves outside the sandbox and was refused."
            )

        return candidate

    def write_file(self, relative_path: str, content: str) -> str:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents = True, exist_ok = True)
        target.write_text(content, encoding = "utf-8")
        return str(target.relative_to(self._root))

    def read_file(self, relative_path: str) -> str:
        target = self.resolve(relative_path)

        if not target.is_file():
            raise FileNotFoundError(f"'{relative_path}' does not exist in the sandbox.")
        if target.stat().st_size > self.MAX_FILE_BYTES:
            raise ValueError(
                f"'{relative_path}' exceeds {self.MAX_FILE_BYTES} bytes and was not read."
            )

        return target.read_text(encoding = "utf-8", errors = "replace")

    def list_files(self) -> list[str]:
        return sorted(str(current.relative_to(self._root)) for current in self._walk())

    def _walk(self) -> Iterator[pathlib.Path]:
        for current in self._root.rglob("*"):
            if not current.is_file():
                continue
            if any(part in self.SKIPPED_DIRECTORIES for part in current.parts):
                continue
            if current.stat().st_size > self.MAX_FILE_BYTES:
                continue
            yield current

    def run(self, command: str, timeout_seconds: int = 60) -> SandboxCommandResult:
        raise RuntimeError(
            "This sandbox cannot run commands — it is a bare host directory with no "
            "isolation. Start the Docker-backed pool to give agents an environment "
            "where executing their own code is contained."
        )
