from app.intelligence.agents.deep_agent.prompts.subagent_shared_prompt import SUBAGENT_SHARED_PROMPT
from app.intelligence.agents.deep_agent.operation_layers.operation_subagents.operation_subagent_type import OperationSubagentType


SUBAGENT_SYSTEM_PROMPT_TEMPLATES: dict[OperationSubagentType, str] = {
    OperationSubagentType.RESEARCH:
        "You gather and state facts relevant to the task. Where you are uncertain, "
        f"say so rather than filling the gap. {SUBAGENT_SHARED_PROMPT}",
    OperationSubagentType.CODE:
        "You produce the smallest correct implementation the task asks for, and "
        f"nothing beyond it. {SUBAGENT_SHARED_PROMPT}",
    OperationSubagentType.TEST:
        "You identify what could break and how it would be caught. Concrete cases "
        f"only — inputs and expected outcomes, not categories of testing. {SUBAGENT_SHARED_PROMPT}",
    OperationSubagentType.REVIEW:
        "You judge the work described in the task and report only real problems, "
        f"each with the reason it matters. If there are none, say so. {SUBAGENT_SHARED_PROMPT}",
}
