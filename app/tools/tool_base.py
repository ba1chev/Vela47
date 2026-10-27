from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

TInput = TypeVar("TInput", bound = BaseModel)
TOutput = TypeVar("TOutput")


class ToolBase(ABC, Generic[TInput, TOutput]):
    """Abstract base for every tool the agent can invoke. TInput must be a
    Pydantic BaseModel so its JSON schema can be extracted and passed to the
    model at inference time, and so MessageToolCall.args can be validated
    against it before execution. TOutput is unconstrained — tools may return
    any Python object; the ToolExecutor serialises it into a MessageTool."""

    def __init__(self, function_predicate: Callable[..., TOutput]) -> None:
        self._function_predicate = function_predicate

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier the model uses to refer to this tool. Must match
        exactly the name declared in the tools schema sent to the model."""
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable explanation of what the tool does, shown to the model
        so it can decide when and how to invoke it."""
        raise NotImplementedError("Must be implemented")

    @property
    @abstractmethod
    def input_schema(self) -> type[TInput]:
        """The Pydantic model class that defines the tool's input structure.
        Used to validate MessageToolCall.args and to generate the JSON schema
        passed to the model in the tools list."""
        raise NotImplementedError("Must be implemented")

    @abstractmethod
    def execute(self, input: TInput) -> TOutput:
        raise NotImplementedError("Must be implemented")
