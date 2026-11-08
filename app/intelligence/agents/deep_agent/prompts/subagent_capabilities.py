from app.intelligence.agents import OperationSubagentType


SUBAGENT_CAPABILITIES: dict[OperationSubagentType, str] = {
    OperationSubagentType.RESEARCH:
        "finds information. It searches the web — and the user's documents and workspace "
        "when there are any — reads pages and reports facts with their sources. It cannot "
        "create or change files.",
    OperationSubagentType.CODE:
        "writes code. It reads the workspace and creates or edits files. Use it for every "
        "step that creates or changes a file.",
    OperationSubagentType.TEST:
        "tests code. It writes pytest tests for code in the workspace and runs them. Use it "
        "for every step about tests or about checking that code works.",
    OperationSubagentType.REVIEW:
        "reviews code. It reads existing files and reports problems. It cannot write or run "
        "anything, so use it only to inspect files another step creates or that already exist.",
}


def format_subagent_capabilities() -> str:
    return "\n".join(
        f"- {current_type.name} {SUBAGENT_CAPABILITIES[current_type]}"
        for current_type in OperationSubagentType
    )
