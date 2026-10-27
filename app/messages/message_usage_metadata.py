from pydantic import Field

from app.messages.message_base.message_immutable_model import MessageImmutableModel


class MessageUsageMetadata(MessageImmutableModel):
    """Token consumption snapshot for a single model response, as reported by the model
    server. Used to enforce input/output limits defined in ModelConfig, estimate per-request
    cost, and feed monitoring dashboards. Attached to AIMessage only; absent when the
    provider did not return usage information."""
    input_tokens: int = Field(
        description = "Number of tokens in the full prompt sent to the model — including the "
            "system message, conversation history, retrieved context, and tool definitions. "
            "Used to check against max_input_tokens limits and estimate cost."
    )
    output_tokens: int = Field(
        description = "Number of tokens the model generated in its response. Counts only the "
            "completion, not the prompt. Capped by max_output_tokens when that field is set "
            "in ModelConfig."
    )
    total_tokens: int = Field(
        description = "Sum of input_tokens and output_tokens. Provided as a convenience field; "
            "equals input_tokens + output_tokens. Use this when billing or rate-limit logic "
            "needs the combined request size."
    )
