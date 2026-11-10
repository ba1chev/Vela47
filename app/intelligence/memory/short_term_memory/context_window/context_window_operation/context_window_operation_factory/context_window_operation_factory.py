from typing import Any

from app.intelligence.memory import ContextWindowOperation
from app.intelligence.memory import ContextWindowOperationType
from app.intelligence.memory import CONTEXT_WINDOW_OPERATION_REGISTRY
from app.intelligence.memory import ContextWindowOperationBaseFactory


class ContextWindowOperationFactory(ContextWindowOperationBaseFactory):
    """Concrete factory that maps each ContextWindowOperationType to its
    ContextWindowOperation subclass through CONTEXT_WINDOW_OPERATION_REGISTRY and
    delegates construction to it. Additional keyword arguments are forwarded verbatim,
    so callers can supply operation-specific parameters, such as SLIDE's step or
    SUMMARIZE's summarizer, without the factory knowing about them."""

    def create(self, type: ContextWindowOperationType, **kwargs: Any) -> ContextWindowOperation:
        cls = CONTEXT_WINDOW_OPERATION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No operation class registered for type '{type}'. "
                f"Known types: {list(self._registry)}"
            )

        return cls(**kwargs)
