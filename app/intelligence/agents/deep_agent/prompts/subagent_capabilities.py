from app.intelligence.agents import OperationSubagentType


SUBAGENT_CAPABILITIES: dict[OperationSubagentType, str] = {
    OperationSubagentType.RESEARCH:
        "can search the workspace and report what is already there. "
        "It cannot create or change anything.",
    OperationSubagentType.CODE:
        "can write one implementation file. "
        "Use it for any step whose output is working code.",
    OperationSubagentType.TEST:
        "can write one test file. "
        "Use it for any step that asks for tests — never assign tests to REVIEW.",
    OperationSubagentType.REVIEW:
        "can read one existing file and judge it. "
        "It cannot write anything, so only assign it a step that inspects work "
        "another step already produced.",
}


def format_subagent_capabilities() -> str:
    return "\n".join(
        f"- {current_type.name}: {SUBAGENT_CAPABILITIES[current_type]}"
        for current_type in OperationSubagentType
    )
