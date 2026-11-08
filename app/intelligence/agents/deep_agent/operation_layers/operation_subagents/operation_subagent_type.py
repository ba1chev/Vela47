from enum import Enum


class OperationSubagentType(str, Enum):
    """Enumerates the kinds of subagent a plan step can be assigned to. The type
    is the single discriminator that determines how a subagent is built — which
    tool it is given, which model and sampling profile it runs on, and how its
    context window is managed. OperationSubagentFactory resolves the type into a
    fully configured OperationSubagent; the layers themselves never branch on it.

    The values are the names. The planner writes the type into its JSON plan, and
    the prompt describes the types by name — with numbers for values, a small model
    had to remember that CODE is 2, and a wrong guess sent a step that writes a file
    to a subagent that cannot write."""

    RESEARCH = "RESEARCH"
    CODE = "CODE"
    TEST = "TEST"
    REVIEW = "REVIEW"
