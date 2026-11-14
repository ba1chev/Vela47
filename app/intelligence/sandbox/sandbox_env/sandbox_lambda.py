import json
import base64
import pathlib
from typing import Any

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import cap_sandbox_output
from app.intelligence.sandbox import SandboxCommandResult
from app.intelligence.sandbox import archive_sandbox_directory


class SandboxLambda(SandboxEnv):
    """A Lambda function that a subagent's commands run in, over a copy of its run's
    directory, the production counterpart of SandboxDocker. File operations stay in that
    directory on the server, and only run() reaches the function: the directory travels
    gzipped in the request, the command runs in a fresh workspace there, and the output
    comes back. Nothing a command writes returns.

    Each invocation runs in a Firecracker microVM with no network route out, and the
    function clears its workspace and processes before it answers, because Lambda
    reuses a warm environment for the next request. Lambda takes at most 6 MB per
    request, so a larger workspace is refused here rather than failing there."""

    MAX_PAYLOAD_BYTES = 6_000_000

    def __init__(self, function_name: str, host_directory: pathlib.Path, client: Any,
        identifier: str) -> None:
        self._function_name: str = function_name
        self._client: Any = client
        self._files: SandboxEnvLocal = SandboxEnvLocal(root = host_directory, identifier = identifier)

    @property
    def identifier(self) -> str:
        return self._files.identifier

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
        payload = json.dumps({
            "archive": base64.b64encode(archive_sandbox_directory(self._files.root, compress = True)).decode(),
            "command": command,
            "timeout_seconds": timeout_seconds
        }).encode()
        if len(payload) > self.MAX_PAYLOAD_BYTES:
            return SandboxCommandResult(
                exit_code = -1,
                output = f"The workspace is too large to run a command on ({len(payload) // 1_000_000} MB, "
                    f"the sandbox takes at most {self.MAX_PAYLOAD_BYTES // 1_000_000} MB)."
            )

        try:
            response = self._client.invoke(FunctionName = self._function_name, Payload = payload)
            answer = json.loads(response["Payload"].read())
        except Exception as error:
            return SandboxCommandResult(exit_code = -1, output = f"The sandbox could not be reached: {error}")

        if response.get("FunctionError"):
            return SandboxCommandResult(
                exit_code = -1,
                output = f"The sandbox failed: {answer.get('errorMessage', answer) if isinstance(answer, dict) else answer}"
            )
        return SandboxCommandResult(
            exit_code = answer["exit_code"],
            output = cap_sandbox_output(answer["output"]),
            timed_out = answer.get("timed_out", False)
        )
