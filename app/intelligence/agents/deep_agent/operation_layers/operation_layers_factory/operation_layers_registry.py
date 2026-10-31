from app.intelligence.agents import OperationType
from app.intelligence.agents import OperationLayerBase
from app.intelligence.agents import OperationMergingLayer
from app.intelligence.agents import OperationPlanningLayer
from app.intelligence.agents import OperationSubagentsLayer
from app.intelligence.agents import OperationDecompositionLayer


OPERATION_LAYERS_REGISTRY: dict[OperationType, type[OperationLayerBase]] = {
    OperationType.PLANNING: OperationPlanningLayer,
    OperationType.DECOMPOSITION: OperationDecompositionLayer,
    OperationType.SUBAGENTS: OperationSubagentsLayer,
    OperationType.MERGING: OperationMergingLayer
}
