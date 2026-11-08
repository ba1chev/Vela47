import hashlib

from app.intelligence.sandbox import SandboxEnv
from app.intelligence.messages import MessageBase
from app.intelligence.agents import OperationSubagentProbeBase


class OperationSubagentProbeWorkspace(OperationSubagentProbeBase):
    """Reports which files a step really created or changed, by comparing the workspace
    before the subagent starts with the workspace after it finishes — whatever the
    subagent says it wrote, and however it wrote it.

    The workspace belongs to the whole run, so the comparison is what isolates this
    step: files an earlier step left are in both snapshots and are not reported again.
    A step that changed nothing is reported as such, because a coding step that only
    described its code is exactly what this probe exists to catch."""

    MAX_LISTED = 10

    def __init__(self, sandbox_env: SandboxEnv) -> None:
        super().__init__(sandbox_env)
        self._before: dict[str, str] = {}

    def _snapshot(self) -> dict[str, str]:
        snapshot = {}
        for current_path in self._sandbox_env.list_files():
            try:
                snapshot[current_path] = self._sandbox_env.read_file(current_path)
            except (OSError, ValueError):
                continue
        return snapshot

    def _lines(self, content: str) -> str:
        count = len(content.splitlines())
        return f"{count} line" if count == 1 else f"{count} lines"

    def _listed(self, paths: list[str], contents: dict[str, str]) -> str:
        listed = ", ".join(
            f"{current_path} ({self._lines(contents[current_path])})"
            for current_path in paths[:self.MAX_LISTED]
        )
        extra = len(paths) - self.MAX_LISTED
        return listed + (f" and {extra} more" if extra > 0 else "")

    def before(self) -> None:
        self._before = {
            current_path: hashlib.sha256(current_content.encode("utf-8")).hexdigest()
            for current_path, current_content in self._snapshot().items()
        }

    def after(self, messages: list[MessageBase]) -> list[str]:
        current = self._snapshot()
        created = sorted(current_path for current_path in current if current_path not in self._before)
        changed = sorted(
            current_path for current_path in current
            if current_path in self._before
            and hashlib.sha256(current[current_path].encode("utf-8")).hexdigest() != self._before[current_path]
        )

        if not created and not changed:
            return ["No file in the workspace was created or changed in this step."]
        facts = []
        if created:
            facts.append(f"Files created: {self._listed(created, current)}.")
        if changed:
            facts.append(f"Files changed: {self._listed(changed, current)}.")
        return facts
