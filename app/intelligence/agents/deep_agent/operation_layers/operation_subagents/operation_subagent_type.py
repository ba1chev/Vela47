from enum import Enum


class OperationSubagentType(Enum):
    """Enumerates the kinds of subagent a plan step can be assigned to. The type
    is the single discriminator that determines how a subagent is built — which
    tool it is given, which model and sampling profile it runs on, and how its
    context window is managed. OperationSubagentFactory resolves the type into a
    fully configured OperationSubagent; the layers themselves never branch on it."""

    RESEARCH = 1
    CODE = 2
    TEST = 3
    REVIEW = 4
