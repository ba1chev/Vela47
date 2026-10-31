from typing import Any
from abc import ABC, abstractmethod

from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation import ContextWindowOperation
from app.intelligence.memory.short_term_memory.context_window.context_window_operation.context_window_operation_type import ContextWindowOperationType


class ContextWindowOperationBaseFactory(ABC):
    """Abstract factory that defines the contract for instantiating
    ContextWindowOperation objects. Subclasses implement create() to map each
    ContextWindowOperationType to its concrete class, keeping the operation
    pipeline decoupled from individual operation implementations."""

    @abstractmethod
    def create(self, type: ContextWindowOperationType, **kwargs: Any) -> ContextWindowOperation:
        raise NotImplementedError("Must be implemented")
