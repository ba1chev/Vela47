from app.intelligence.messages import MessageAI
from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationLayerBase


class CapturingLayer(OperationLayerBase):
    """Keeps every context it is handed, so a test can see exactly what reached the
    pipeline — the history a DeepAgent passed along, for one — and can answer with a
    fixed reply so the agent has a turn to remember."""

    def __init__(self, contexts, answer = None) -> None:
        self._contexts = contexts
        self._answer = answer

    @property
    def operation_type(self) -> OperationType:
        return OperationType.MERGING

    def execute(self, context) -> None:
        self._contexts.append(context)
        if self._answer is not None:
            context.final = MessageAI(content = self._answer)
