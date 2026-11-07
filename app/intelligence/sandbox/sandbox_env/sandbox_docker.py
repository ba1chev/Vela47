import pathlib
import subprocess

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import SandboxCommandResult


class SandboxDocker(SandboxEnv):
    """A container that a subagent's commands run inside, over a directory shared
    with the host.

    File operations do not go through the daemon. The run directory is bind mounted
    into the container, so writing on the host is the same bytes the container reads
    — which avoids a round trip per file, sidesteps escaping content through `docker
    cp`, and leaves the artefacts browsable after the run. Only run() needs Docker,
    and that is the one operation that genuinely requires containment.

    The container is leased, the directory is not. Containers are leased per task so
    several can work at once; the directory belongs to the whole run, so a file one
    subagent writes is still there for the next. Tying the filesystem to the lease
    instead would delete a CODE subagent's work before a REVIEW subagent could read it.

    The command string comes from a model and is passed as a single argument to a
    shell *inside* the container — never to a host shell. The blast radius of
    anything it does is the container and the mounted run directory.

    Long output loses its middle, not its end. A test runner, a compiler and a crashing
    script all say what went wrong last, so the end is kept in full and only a short
    head survives alongside it."""

    MAX_OUTPUT_CHARS = 8_000
    KEPT_HEAD_CHARS = 2_000

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

    def run(self, command: str, timeout_seconds: int = 60) -> SandboxCommandResult:
        try:
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

        output = (completed.stdout or "") + (completed.stderr or "")
        if len(output) > self.MAX_OUTPUT_CHARS:
            kept_tail = self.MAX_OUTPUT_CHARS - self.KEPT_HEAD_CHARS
            output = (
                output[:self.KEPT_HEAD_CHARS]
                + f"\n… {len(output) - self.MAX_OUTPUT_CHARS} characters of output cut …\n"
                + output[-kept_tail:]
            )

        return SandboxCommandResult(
            exit_code = completed.returncode,
            output = output.strip() or "(no output)"
        )
