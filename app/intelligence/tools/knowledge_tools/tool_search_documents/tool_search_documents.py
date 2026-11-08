from typing import Optional

from app.intelligence.tools import ToolBase
from app.intelligence.memory import VectorDbMemory
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.memory import VectorDbOperationPolicy
from app.intelligence.tools import ToolSearchDocumentsInput


class ToolSearchDocuments(ToolBase[ToolSearchDocumentsInput, str]):
    """Searches the documents the user uploaded — the same chunks, vectors and hybrid
    search the RAG agent answers from — and returns the best passages with the title of
    the document each came from.

    It gives the deep agent's research steps the user's own material, which is usually
    a better source than the web for anything about the user's own work. The memory is
    handed in already filled for this one request and owner, so the tool can never read
    another user's documents: it has no way to ask for them.

    Passages are cut to a fixed length because several of them go into one context
    window; the title and part number are kept so a finding can be cited."""

    MAX_PASSAGE_CHARS = 900

    def __init__(self, vector_db_memory: VectorDbMemory,
        retrieval_policy: Optional[VectorDbOperationPolicy] = None) -> None:
        super().__init__()
        self._vector_db_memory: VectorDbMemory = vector_db_memory
        self._retrieval_policy: VectorDbOperationPolicy = (
            retrieval_policy if retrieval_policy is not None else HybridSearchPolicy()
        )

    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return (
            "Search the documents the user uploaded and get back the most relevant "
            "passages, each with the document it came from. Use it first for anything the "
            "user's own material may cover, and cite the document title for what you use."
        )

    @property
    def input_schema(self) -> type[ToolSearchDocumentsInput]:
        return ToolSearchDocumentsInput

    def execute(self, input: ToolSearchDocumentsInput) -> str:
        if len(self._vector_db_memory) == 0:
            return "The user has not uploaded any documents, so there is nothing to search."

        entries = self._vector_db_memory.search_entries(input.query, input.top_k, self._retrieval_policy)
        if not entries:
            return f"No passage in the user's documents matches '{input.query}'."

        passages = []
        for index, current_entry in enumerate(entries[:input.top_k], start = 1):
            message = current_entry.message
            content = message.content if isinstance(message.content, str) else str(message.content)
            if len(content) > self.MAX_PASSAGE_CHARS:
                content = content[:self.MAX_PASSAGE_CHARS].rstrip() + " …"
            part = message.additional_kwargs.get("chunk_index")
            source = message.name or "untitled document"
            label = f"{source}, part {part + 1}" if isinstance(part, int) else source
            passages.append(f"[{index}] {label}\n{content}")

        return f"{len(passages)} passage(s) for '{input.query}':\n\n" + "\n\n".join(passages)
