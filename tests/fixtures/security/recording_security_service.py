from app.server.security import SecurityServiceBase


class RecordingSecurityService(SecurityServiceBase):
    """Records that it ran, in order, into a list the test owns — and can be told to
    write a decision or to raise. Lets a pipeline test control every outcome without
    any real token or policy being involved."""

    def __init__(self, security_type, log, label, decision = None, error = None) -> None:
        self._security_type = security_type
        self._log = log
        self._label = label
        self._decision = decision
        self._error = error

    @property
    def security_type(self):
        return self._security_type

    def execute(self, context) -> None:
        self._log.append(self._label)
        if self._error is not None:
            raise self._error
        if self._decision is not None:
            context.decision = self._decision
