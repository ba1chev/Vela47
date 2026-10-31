from pydantic import BaseModel, Field


class SandboxCommandResult(BaseModel):
    """What running a command inside a sandbox produced. A failed command is a
    result, not an exception: the subagent that asked for it is expected to read
    the output and react, so a non-zero exit has to reach the model rather than
    unwind the run."""

    exit_code: int = Field(
        description = "Process exit status. Zero means success; anything else is the command "
            "reporting failure, which the calling agent is expected to interpret rather than "
            "treat as a crash."
    )
    output: str = Field(
        description = "Combined stdout and stderr, truncated to stay within the agent's context "
            "window. Interleaved rather than separated because a test runner's failure detail "
            "is only readable in the order it was written."
    )
    timed_out: bool = Field(
        default = False,
        description = "True when the command was killed for exceeding its time limit. Distinct "
            "from a non-zero exit — the agent learns the work never finished rather than that "
            "it finished badly."
    )
