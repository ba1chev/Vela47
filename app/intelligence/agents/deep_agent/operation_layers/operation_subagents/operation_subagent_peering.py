from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.agents import A2AInteractionType
from app.intelligence.agents import OperationSubagentType


class OperationSubagentPeering(BaseModel):
    """Which subagents of a run may message an earlier one, and how the messages travel.
    The subagents layer keeps the last subagent of every type that can be messaged alive
    with its sandbox slot, and gives a later subagent of a messaging type a
    message_worker tool bound to it through an A2A interaction.

    Plain data, so which pairs talk is decided where the agent is built, like the
    blueprints. A layer without a peering runs every subagent in isolation."""

    model_config = ConfigDict(frozen = True)

    interaction_type: A2AInteractionType = Field(
        description = "How a message travels between the two subagents. DOCKER when their "
            "sandboxes are containers, so the text crosses a network of the pair's own; HOST "
            "when the pool has no containers and the text is handed over in the process."
    )
    peers: dict[OperationSubagentType, OperationSubagentType] = Field(
        description = "For each type that may send messages, the type of the earlier subagent it "
            "messages — TEST and REVIEW message CODE, so a tester or reviewer can have the bug "
            "it found fixed by the worker that wrote the code. A type missing here never sends."
    )
    max_messages: int = Field(
        default = 2,
        ge = 1,
        description = "How many messages one subagent may send in its step. Every message makes "
            "the other subagent run again, so the cap bounds how long a step can take."
    )
