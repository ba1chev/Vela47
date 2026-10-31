from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Callable, Generic, Optional, TypeVar

TInput = TypeVar("TInput", bound = BaseModel)
TOutput = TypeVar("TOutput")


class ToolBase(ABC, Generic[TInput, TOutput]):
    """Abstract base for every tool the agent can invoke. TInput must be a
    Pydantic BaseModel so its JSON schema can be extracted and passed to the
    model at inference time, and so MessageToolCall.args can be validated
    against it before execution. TOutput is unconstrained — tools may return
    any Python object; the ToolExecutor serialises it into a MessageTool."""

    def __init__(self, function_predicate: Optional[Callable[..., TOutput]] = None) -> None:
        self._function_predicate = function_predicate

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def input_schema(self) -> type[TInput]:
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def execute(self, input: TInput) -> TOutput:
        raise NotImplementedError("Must be implemented")
