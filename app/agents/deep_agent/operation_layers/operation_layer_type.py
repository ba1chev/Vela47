from enum import Enum


class OperationType(Enum):
    """Enumerates the stages a DeepAgent pipeline can run. Each value maps to a
    concrete OperationLayerBase subclass registered in OperationLayersFactory.
    The numeric values encode the canonical execution order — PLANNING produces
    the plan, DECOMPOSITION turns it into tasks, SUBAGENTS executes them, and
    MERGING folds the results into a single answer — but the OperationPolicy is
    free to select a subset or reorder them."""

    PLANNING = 0
    DECOMPOSITION = 1
    SUBAGENTS = 2
    MERGING = 3
