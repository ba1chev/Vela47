from typing import Any

from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_factory.context_window_operation_registry import CONTEXT_WINDOW_OPERATION_REGISTRY
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_factory.context_window_operation_base_factory import ContextWindowOperationBaseFactory


class ContextWindowOperationFactory(ContextWindowOperationBaseFactory):
    """Concrete factory that maps each ContextWindowOperationType to its
    corresponding ContextWindowOperation subclass and delegates construction
    to it. Additional keyword arguments are forwarded verbatim, so callers
    can supply operation-specific parameters without the factory needing to
    know about them explicitly.

    Registry reference:
      EXPAND    -> ContextWindowOperationExpand()
      SHRINK    -> ContextWindowOperationShrink(n=<int>)
      SLIDE     -> ContextWindowOperationSlide(step=<int>, default 1)
      SUMMARIZE -> ContextWindowOperationSummarize(n=<int>, summarizer=<Callable>)
      TRUNCATE  -> ContextWindowOperationTruncate(max_chars=<int>)
      FLATTEN   -> ContextWindowOperationFlatten()"""

    def create(self, type: ContextWindowOperationType, **kwargs: Any) -> ContextWindowOperation:
        cls = CONTEXT_WINDOW_OPERATION_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No operation class registered for type '{type}'. "
                f"Known types: {list(self._registry)}"
            )

        return cls(**kwargs)
