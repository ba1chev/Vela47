from typing import Optional
from time import perf_counter

from app.intelligence.model import ModelClientBase
from app.intelligence.tracing import TraceEventType
from app.intelligence.model import ModelClientOllama
from app.intelligence.tracing import TracingServiceBase
from app.intelligence.tracing import current_tracing_service


class ModelEmbeddings:
    """Generates dense vector representations of text with an embedding model, served
    by an injected ModelClientBase, a local Ollama server unless told otherwise. Each
    vector is a fixed-length list of floats whose dimensionality depends on the model.

    embed_many() sends texts in batches rather than one request each. Indexing a
    document means embedding dozens of chunks, and a round trip per chunk would dominate
    the time it takes; embed() is the single-text case of the same call.

    Every request is reported as a MODEL_INVOKED event, the same event ModelFoundation
    emits, to the injected tracer or, for an instance shared by the process, to the run
    using it (see current_tracing_service). Instances hold nothing but the model name
    and the tracer and can be shared safely across threads."""

    BATCH_SIZE = 64

    def __init__(self, model_name: str, tracing_service: Optional[TracingServiceBase] = None,
        keep_alive: str = "30m", client: Optional[ModelClientBase] = None) -> None:
        self._model_name: str = model_name
        self._keep_alive: str = keep_alive
        self._client: ModelClientBase = client if client is not None else ModelClientOllama()
        self._tracing_service: Optional[TracingServiceBase] = tracing_service

    @property
    def model_name(self) -> str:
        return self._model_name

    def _tracer(self) -> TracingServiceBase:
        return self._tracing_service if self._tracing_service is not None else current_tracing_service()

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []

        for start in range(0, len(texts), self.BATCH_SIZE):
            batch = texts[start:start + self.BATCH_SIZE]
            began = perf_counter()
            batch_vectors, input_tokens = self._client.embed(self._model_name, batch, self._keep_alive)
            vectors.extend(batch_vectors)

            self._tracer().emit(
                TraceEventType.MODEL_INVOKED,
                self._model_name,
                {
                    "input_tokens": input_tokens,
                    "output_tokens": 0,
                    "total_tokens": input_tokens,
                    "tool_calls": [],
                    "inputs": len(batch),
                    "embedding": True
                },
                (perf_counter() - began) * 1000.0
            )

        return vectors

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]
