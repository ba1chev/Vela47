from typing import Optional
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model_name: str = Field(
        description = "Name of the large language model exactly as it appears in `ollama list`, "
            "including the tag (e.g. 'qwen3:4b'). Determines which model handles the request."
    )
    max_input_tokens: Optional[int] = Field(
        default = None,
        gt = 0,
        description = "Maximum number of tokens the model may receive as input (prompt, history and "
            "retrieved context combined). Used to trim or summarize content before sending. "
            "None means no explicit limit beyond the model's context window."
    )
    max_output_tokens: Optional[int] = Field(
        default = None,
        gt = 0,
        description = "Maximum number of tokens the model may generate in a single response. "
            "Generation stops once this limit is reached, even mid-sentence. "
            "None means the model generates until it finishes naturally."
    )
    timeout: float = Field(
        default = 120.0,
        gt = 0,
        description = "Maximum time in seconds to wait for a response from the Ollama server before "
            "the request is aborted. Should be higher for large models, long outputs or "
            "when reasoning mode is enabled."
    )
    temperature: float = Field(
        default = 0.7,
        ge = 0.0,
        le = 2.0,
        description = "Controls randomness of the output. Low values (0.0-0.3) make responses focused "
            "and deterministic, suitable for planning and data extraction. Higher values "
            "(0.7-1.0) make them more varied and creative."
    )
    top_p: float = Field(
        default = 0.9,
        gt = 0.0,
        le = 1.0,
        description = "Nucleus sampling threshold. The model samples only from the smallest set of "
            "tokens whose cumulative probability reaches this value. Lower values restrict "
            "choices to the most likely tokens."
    )
    top_k: int = Field(
        default = 40,
        gt = 0,
        description = "Limits sampling to the K most likely next tokens. Lower values make the output "
            "more conservative and predictable, higher values allow more diversity."
    )
    repeat_penalty: float = Field(
        default = 1.1,
        gt = 0.0,
        description = "Penalty applied to tokens that have already appeared in the output. Values above "
            "1.0 discourage repetition, values below 1.0 encourage it. Small models often "
            "need a slightly higher value to avoid loops."
    )
    seed: Optional[int] = Field(
        default = None,
        description = "Random seed for sampling. With a fixed seed and identical input, the model "
            "produces the same output, which is useful for testing and evaluation. "
            "None means a different random seed on every request."
    )
    stop: Optional[list[str]] = Field(
        default = None,
        description = "List of sequences at which generation stops immediately. The stop sequence "
            "itself is not included in the output. None means no custom stop sequences."
    )
    think: bool = Field(
        default = False,
        description = "Enables reasoning mode for models that support it (e.g. Qwen3). The model "
            "reasons step by step before answering, which improves planning and complex "
            "tasks but significantly increases latency and token usage."
    )
    keep_alive: str = Field(
        default = "30m",
        description = "How long the model stays loaded in memory after the last request, as a "
            "duration string (e.g. '5m', '1h'). Keeping it loaded avoids slow reloads "
            "between requests. '0' unloads immediately, '-1' keeps it loaded indefinitely."
    )