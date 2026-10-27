import ollama


class ModelEmbeddings:
    """Generates dense vector representations of text using an Ollama embedding
    model. Each call to embed() sends the text to the local Ollama server and
    returns a fixed-length list of floats whose dimensionality depends on the
    chosen model. Instances are stateless beyond the model name and can be
    shared safely across threads."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def embed(self, text: str) -> list[float]:
        response = ollama.embeddings(
            model = self._model_name, prompt = text
        )
        return response["embedding"]
