from typing import Optional
from pydantic import BaseModel, Field

from app.intelligence.messages.message_ai import MessageAI
from app.intelligence.messages.message_human import MessageHuman
from app.intelligence.agents.deep_agent.operation_layers.operation_planning.operation_plan import OperationPlan
from app.intelligence.agents.deep_agent.operation_layers.operation_decomposition.operation_task import OperationTask
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_result import OperationSubagentResult


class OperationContext(BaseModel):
    """The single mutable object threaded through every layer of an
    OperationPipeline. Each layer reads the fields it depends on and writes the
    one it owns — planning writes plan, decomposition writes tasks, subagents
    writes results, merging writes final. Because every layer sees the whole
    accumulated state rather than just its predecessor's return value, late
    layers keep access to early data: merging can weigh results against the
    original goal and the plan that requested them. Unlike the message models
    this is intentionally not frozen — mutation in place is the mechanism by
    which layers communicate."""

    goal: MessageHuman = Field(
        description = "The request that started this run, exactly as it reached the DeepAgent. "
            "Never overwritten by a layer, so it stays available as ground truth for every "
            "stage no matter how far the plan has drifted."
    )
    plan: Optional[OperationPlan] = Field(
        default = None,
        description = "The planning layer's breakdown of the goal into ordered steps. None until "
            "that layer has run, which is also how a pipeline configured without a planning "
            "stage signals that downstream layers must work from the goal alone."
    )
    tasks: list[OperationTask] = Field(
        default_factory = list,
        description = "Dispatchable tasks derived from the plan by the decomposition layer. "
            "Empty until that layer runs; its length is what determines how many subagents "
            "the subagents layer will create."
    )
    results: list[OperationSubagentResult] = Field(
        default_factory = list,
        description = "One entry per executed task, appended by the subagents layer as each "
            "subagent finishes. Holds both successes and failures so the merging layer sees "
            "the complete picture."
    )
    final: Optional[MessageAI] = Field(
        default = None,
        description = "The merged answer the DeepAgent returns to its caller. None until the "
            "merging layer has run; the pipeline treats this field as its return value."
    )
