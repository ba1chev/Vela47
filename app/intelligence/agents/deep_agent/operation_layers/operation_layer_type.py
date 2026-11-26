from enum import Enum


class OperationType(Enum):
    """Enumerates the stages a DeepAgent pipeline can run. Each value maps to a
    concrete OperationLayerBase subclass registered in OperationLayersFactory.
    The numeric values encode the canonical execution order — SECURITY inspects what
    the run starts from, PLANNING produces the plan, DECOMPOSITION turns it into tasks,
    SUBAGENTS executes them, and MERGING folds the results into a single answer — but
    the OperationPolicy is free to select a subset or reorder them."""

    SECURITY = 0
    PLANNING = 1
    DECOMPOSITION = 2
    SUBAGENTS = 3
    MERGING = 4
