import json
import pathlib
from typing import Any, Optional

from app.intelligence.model import ModelEmbeddings
from app.intelligence.agents import encode_topic_vector


class RagTopicRegisterWriter:
    """Embeds the text of every topic in the register with each of the given models and
    writes the register back as Python, beside this file. Texts are written by hand and
    vectors only ever come from here; vectors of models that were not given are kept, so
    one environment's model can be refreshed without reaching the other's.

    A topic is embedded as a query, through its model's template in query_templates, and
    chunks as passages: an asymmetric model then compares them the way it was trained
    to, as a query and what it retrieves. Vectors are base64 of little-endian float32,
    about a fifth of the size of a written-out list."""

    REGISTER_PATH = pathlib.Path(__file__).with_name("rag_topic_register.py")
    HEADER = (
        "# The general topics a chunk is matched against: each topic's text, written by hand,\n"
        "# and its vector for every embedding model, as base64 of little-endian float32.\n"
        "# Vectors are written by RagTopicRegisterWriter through build_topic_register().\n"
    )

    def __init__(self, embeddings: list[ModelEmbeddings], query_templates: Optional[dict[str, str]] = None,
        path: Optional[pathlib.Path] = None) -> None:
        self._embeddings: list[ModelEmbeddings] = embeddings
        self._query_templates: dict[str, str] = query_templates if query_templates is not None else {}
        self._path: pathlib.Path = path if path is not None else self.REGISTER_PATH

    def _render(self, register: dict[str, dict[str, Any]]) -> str:
        topics = []
        for current_topic, current in register.items():
            vectors = ",\n".join(
                f"            {json.dumps(current_model)}: {json.dumps(current['vectors'][current_model])}"
                for current_model in sorted(current["vectors"])
            )
            topics.append(
                f"    {json.dumps(current_topic, ensure_ascii = False)}: {{\n"
                f"        \"text\": {json.dumps(current['text'], ensure_ascii = False)},\n"
                + (f"        \"vectors\": {{\n{vectors}\n        }}\n" if vectors else "        \"vectors\": {}\n")
                + "    }"
            )
        return (
            f"{self.HEADER}\nfrom typing import Any\n\n"
            "RAG_TOPIC_REGISTER: dict[str, dict[str, Any]] = {\n" + ",\n".join(topics) + "\n}\n"
        )

    def write(self, register: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        topics = list(register)
        updated = {
            current_topic: {"text": register[current_topic]["text"], "vectors": dict(register[current_topic]["vectors"])}
            for current_topic in topics
        }

        for current_embeddings in self._embeddings:
            template = self._query_templates.get(current_embeddings.model_name, "{query}")
            vectors = current_embeddings.embed_many([
                template.format(query = updated[current_topic]["text"]) for current_topic in topics
            ])
            for current_topic, current_vector in zip(topics, vectors):
                updated[current_topic]["vectors"][current_embeddings.model_name] = encode_topic_vector(current_vector)

        self._path.write_text(self._render(updated), encoding = "utf-8")
        return updated
