from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationLayerBase


class RecordingLayer(OperationLayerBase):
    """Records that it ran, in order, into a list the test owns. Lets a pipeline test
    assert on sequencing without any layer doing real work."""

    def __init__(self, operation_type, log, label) -> None:
        self._operation_type = operation_type
        self._log = log
        self._label = label

    @property
    def operation_type(self) -> OperationType:
        return self._operation_type

    def execute(self, context) -> None:
        self._log.append(self._label)
