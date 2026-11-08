from app.intelligence.agents import OperationSubagentType


SUBAGENT_CAPABILITIES: dict[OperationSubagentType, str] = {
    OperationSubagentType.RESEARCH:
        "can search the user's uploaded documents, the workspace and the web, and read web "
        "pages. It cannot create or change anything.",
    OperationSubagentType.CODE:
        "can read the workspace and create or edit implementation files. "
        "Use it for any step whose output is working code.",
    OperationSubagentType.TEST:
        "can write test files and run them. "
        "Use it for any step that asks for tests or for checking that code works — never "
        "assign tests to REVIEW.",
    OperationSubagentType.REVIEW:
        "can read and search existing files and judge them. "
        "It cannot write or run anything, so only assign it a step that inspects work "
        "another step already produced.",
}


def format_subagent_capabilities() -> str:
    return "\n".join(
        f"- {current_type.name}: {SUBAGENT_CAPABILITIES[current_type]}"
        for current_type in OperationSubagentType
    )
