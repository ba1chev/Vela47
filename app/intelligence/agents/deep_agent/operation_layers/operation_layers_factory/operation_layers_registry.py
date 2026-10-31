from app.intelligence.agents.deep_agent.operation_layers.operation_layer_type import OperationType
from app.intelligence.agents.deep_agent.operation_layers.operation_layer_base import OperationLayerBase
from app.intelligence.agents.deep_agent.operation_layers.operation_merging.operation_merging_layer import OperationMergingLayer
from app.intelligence.agents.deep_agent.operation_layers.operation_planning.operation_planning_layer import OperationPlanningLayer
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_layer_subagents import OperationSubagentsLayer
from app.intelligence.agents.deep_agent.operation_layers.operation_decomposition.operation_decomposition_layer import OperationDecompositionLayer


OPERATION_LAYERS_REGISTRY: dict[OperationType, type[OperationLayerBase]] = {
    OperationType.PLANNING: OperationPlanningLayer,
    OperationType.DECOMPOSITION: OperationDecompositionLayer,
    OperationType.SUBAGENTS: OperationSubagentsLayer,
    OperationType.MERGING: OperationMergingLayer
}
