import io
import shlex
import pathlib
import tarfile
import subprocess
from typing import Optional

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import SandboxCommandResult


class SandboxDocker(SandboxEnv):
    """A container that a subagent's commands run inside, over a copy of its run's
    directory.

    File operations do not go through the daemon. The run's files live in a directory
    on the host and are written and read there directly — which avoids a round trip per
    file and leaves the artefacts browsable after the run. Only run() needs Docker, and
    that is the one operation that genuinely requires containment.

    A container holds one run's files, and only while a command runs. Before each
    command the run's directory is copied into the container's workspace, and after it
    the workspace is deleted. The containers are shared by every user's runs, so
    mounting the directory that holds all of them would let code written for one user
    read what was written for every other; a copy made for one command cannot. The copy
    travels as a tar archive on the exec's stdin — one call to the daemon, no temporary
    file — and the workspace is emptied first, so nothing a failed clean-up left behind
    reaches the next run. What a command writes stays in the copy and goes with it: a
    test run leaves the workspace exactly as the agents left it.

    The container is leased, the directory is not. Containers are leased per task so
    several can work at once; the directory belongs to the whole run, so a file one
    subagent writes is still there for the next. Tying the filesystem to the lease
    instead would delete a CODE subagent's work before a REVIEW subagent could read it.

    The command string comes from a model and is passed as a single argument to a
    shell *inside* the container — never to a host shell. The blast radius of
    anything it does is the container and a throwaway copy of the run's directory.

    Long output loses its middle, not its end. A test runner, a compiler and a crashing
    script all say what went wrong last, so the end is kept in full and only a short
    head survives alongside it.

    Nothing a command starts outlives it. A timeout on `docker exec` stops only the CLI
    on the host — the process inside the container keeps running — and a test can leave
    a child behind when it ends, so after every command each process in the container
    except its keep-alive is killed, and the workspace is deleted with them. The
    container is leased to one subagent at a time, so nothing of anyone else's is
    running there; without the sweep, one infinite loop would take the container's
    single CPU from every task leased this slot afterwards."""

    MAX_OUTPUT_CHARS = 8_000
    KEPT_HEAD_CHARS = 2_000
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

    def _archive(self) -> bytes:
        buffer = io.BytesIO()
        with tarfile.open(fileobj = buffer, mode = "w") as archive:
            archive.add(self._files.root, arcname = ".")
        return buffer.getvalue()

    def _copy_in(self) -> Optional[str]:
        workspace = shlex.quote(self._container_directory)
        try:
            copied = subprocess.run(
                [
                    "docker", "exec", "-i", self._container_name, "sh", "-c",
                    f"rm -rf {workspace} && mkdir -p {workspace} && tar -x -C {workspace}"
                ],
                input = self._archive(),
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
