from app.intelligence.memory import MemoryBase
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageBase
from app.intelligence.model import ModelEmbeddings
from app.intelligence.messages import MessageFactory
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.messages import MessageFactoryBase
from app.intelligence.memory import VectorDbOperationPolicy
from app.intelligence.memory import VectorDbOperationManager


class VectorDbMemory(MemoryBase):
    """Vector store for long-term agent memory. Each message is embedded at insertion
    and kept as a VectorDbMemoryEntry beside its source message, and retrieval runs the
    operations a VectorDbOperationPolicy resolves. Entries embedded earlier, read back
    from a database, are loaded with add_entries() and never embedded twice;
    search_entries() returns entries with their vectors for a caller that reranks them.

    query_template exists for asymmetric embedding models that expect an instruction on
    queries only. It shapes the query vector alone, and keyword operations get the plain
    query text."""

    def __init__(self, embeddings: ModelEmbeddings, query_template: str = "{query}") -> None:
        self._embeddings: ModelEmbeddings = embeddings
        self._query_template: str = query_template
        self._messages_factory: MessageFactoryBase = MessageFactory()
        self._operation_manager: VectorDbOperationManager = VectorDbOperationManager()
        self._entries: list[VectorDbMemoryEntry] = []

    def append_message(self, message: str, message_type: MessageType) -> None:
        msg = self._messages_factory.create(message_type, message)
        vector = self._embeddings.embed(message)
        self._entries.append(VectorDbMemoryEntry(message = msg, vector = vector))

    def add_entries(self, entries: list[VectorDbMemoryEntry]) -> None:
        self._entries.extend(entries)

    def get_message(self, index: int) -> MessageBase:
        if index < 0 or index >= len(self._entries):
            raise IndexError(f"Index {index} is out of range for store of size {len(self._entries)}")
        return self._entries[index].message

    def search_entries(self, query: str, top_k: int,
        policy: VectorDbOperationPolicy) -> list[VectorDbMemoryEntry]:
        if not self._entries:
            return []

        query_vector = self._embeddings.embed(self._query_template.format(query = query))
        operations = policy.resolve(self._entries, query, query_vector, top_k)
        return self._operation_manager.apply(operations, self._entries)

    def search(self, query: str, top_k: int,
        policy: VectorDbOperationPolicy) -> list[MessageBase]:
        return [entry.message for entry in self.search_entries(query, top_k, policy)]

    def __len__(self) -> int:
        return len(self._entries)
