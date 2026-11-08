from app.intelligence.agents import OperationSubagentProbeBase


class RecordingProbe(OperationSubagentProbeBase):
    """A probe that checks nothing and records when it ran and what it was shown, so a
    test can prove the probes run around a subagent's loop and their facts become its
    evidence. Its one fact names the sandbox it was bound to, which is how a factory test
    proves each probe was built for the task's own sandbox."""

    def __init__(self, sandbox_env, log = None) -> None:
        super().__init__(sandbox_env)
        self.log = log if log is not None else []
        self.seen = []

    def before(self) -> None:
        self.log.append("before")

    def after(self, messages):
        self.log.append("after")
        self.seen = list(messages)
        return [f"checked {self._sandbox_env.identifier}"]
