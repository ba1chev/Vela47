from app.intelligence.sandbox import SandboxEnvLocal
from app.intelligence.sandbox import SandboxCommandResult


class ScriptedSandboxEnv(SandboxEnvLocal):
    """A real sandbox directory whose run() answers from a script instead of a container,
    recording every command and its timeout — so a tool that runs commands can be tested
    for what it asks and how it reads the answer, without Docker. With the script
    exhausted it answers as a passing pytest run would."""

    def __init__(self, root, results = None) -> None:
        super().__init__(root, identifier = "scripted")
        self._results = list(results or [])
        self.commands = []

    def run(self, command, timeout_seconds = 60):
        self.commands.append((command, timeout_seconds))
        if self._results:
            return self._results.pop(0)
        return SandboxCommandResult(exit_code = 0, output = "1 passed in 0.01s")
