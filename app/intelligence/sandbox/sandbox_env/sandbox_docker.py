import shlex
import pathlib
import subprocess
from typing import Optional

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import cap_sandbox_output
from app.intelligence.sandbox import SandboxCommandResult
from app.intelligence.sandbox import archive_sandbox_directory


class SandboxDocker(SandboxEnv):
    """A container that a subagent's commands run inside, over a copy of its run's
    directory. File operations stay on the host, in that directory, and only run() goes
    through Docker. The container is leased per task while the directory belongs to the
    run, so one subagent's files are there for the next.

    Containers are shared by every user's runs, so each command sees only a copy: the
    run's directory is streamed into the emptied workspace as a tar on the exec's stdin,
    and afterwards every process but the keep-alive is killed and the workspace deleted.
    Nothing a command writes comes back, and nothing it starts outlives it. The command
    runs in a shell inside the container, never on the host, and long output keeps a
    short head and the full tail."""

    COPY_TIMEOUT_SECONDS = 30
    SWEEP_TIMEOUT_SECONDS = 10

    def __init__(self, container_name: str, host_directory: pathlib.Path,
        container_directory: str) -> None:
        self._container_name: str = container_name
        self._container_directory: str = container_directory
        self._files: SandboxEnvLocal = SandboxEnvLocal(
            root = host_directory,
            identifier = container_name
        )

    @property
    def identifier(self) -> str:
        return self._container_name

    @property
    def root(self) -> pathlib.Path:
        return self._files.root

    def write_file(self, relative_path: str, content: str) -> str:
        return self._files.write_file(relative_path, content)

    def read_file(self, relative_path: str) -> str:
        return self._files.read_file(relative_path)

    def list_files(self) -> list[str]:
        return self._files.list_files()

    def _copy_in(self) -> Optional[str]:
        workspace = shlex.quote(self._container_directory)
        try:
            copied = subprocess.run(
                [
                    "docker", "exec", "-i", self._container_name, "sh", "-c",
                    f"rm -rf {workspace} && mkdir -p {workspace} && tar -x -C {workspace}"
                ],
                input = archive_sandbox_directory(self._files.root),
                capture_output = True,
                timeout = self.COPY_TIMEOUT_SECONDS,
                check = False
            )
        except subprocess.TimeoutExpired:
            return f"the copy took longer than {self.COPY_TIMEOUT_SECONDS}s"

        if copied.returncode != 0:
            return copied.stderr.decode("utf-8", errors = "replace").strip() or f"exit code {copied.returncode}"
        return None

    def _sweep(self) -> None:
        workspace = shlex.quote(self._container_directory)
        try:
            subprocess.run(
                ["docker", "exec", self._container_name, "sh", "-c", f"kill -9 -1; rm -rf {workspace}"],
                capture_output = True,
                timeout = self.SWEEP_TIMEOUT_SECONDS,
                check = False
            )
        except (OSError, subprocess.TimeoutExpired):
            return

    def run(self, command: str, timeout_seconds: int = 60) -> SandboxCommandResult:
        try:
            refusal = self._copy_in()
            if refusal is not None:
                return SandboxCommandResult(
                    exit_code = -1,
                    output = f"The workspace could not be copied into the container: {refusal}"
                )

            completed = subprocess.run(
                [
                    "docker", "exec", "-w", self._container_directory,
                    self._container_name, "sh", "-c", command
                ],
                capture_output = True,
                text = True,
                timeout = timeout_seconds,
                check = False
            )
        except subprocess.TimeoutExpired:
            return SandboxCommandResult(
                exit_code = -1,
                output = f"Command exceeded {timeout_seconds}s and was abandoned.",
                timed_out = True
            )
        except FileNotFoundError:
            return SandboxCommandResult(
                exit_code = -1,
                output = "The docker CLI is not available on this host."
            )
        finally:
            self._sweep()

        return SandboxCommandResult(
            exit_code = completed.returncode,
            output = cap_sandbox_output((completed.stdout or "") + (completed.stderr or ""))
        )
