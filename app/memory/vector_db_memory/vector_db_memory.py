from app.memory.memory_base import MemoryBase
from app.messages.message_type import MessageType
from app.messages.message_base.message_base import MessageBase
from app.messages.message_factory.message_factory import MessageFactory
from app.model.model_embeddings.model_embeddings import ModelEmbeddings
from app.messages.message_factory.message_base_factory import MessageFactoryBase
from app.memory.vector_db_memory.vector_db_memory_entry import VectorDbMemoryEntry
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_policy import VectorDbOperationPolicy
from app.memory.vector_db_memory.vector_db_operation.vector_db_operation_manager import VectorDbOperationManager


class VectorDbMemory(MemoryBase):
    """Persistent vector store for long-term agent memory. Each message is
    embedded by a ModelEmbeddings instance at insertion time and stored as a
    VectorDbMemoryEntry alongside its source MessageBase. Retrieval is driven
    by a VectorDbOperationPolicy that resolves an operation pipeline — search,
    filter, rerank, deduplicate — executed by the VectorDbOperationManager.
    Satisfies the MemoryBase contract so it can substitute for any memory
    implementation, while exposing an additional search() method for
    semantic retrieval."""

    def __init__(self, embeddings: ModelEmbeddings) -> None:
        self._embeddings: ModelEmbeddings = embeddings
        self._messages_factory: MessageFactoryBase = MessageFactory()
        self._operation_manager: VectorDbOperationManager = VectorDbOperationManager()
        self._entries: list[VectorDbMemoryEntry] = []

    def append_message(self, message: str, message_type: MessageType) -> None:
        msg = self._messages_factory.create(message_type, message)
        vector = self._embeddings.embed(message)
        self._entries.append(VectorDbMemoryEntry(message = msg, vector = vector))

    def get_message(self, index: int) -> MessageBase:
        if index < 0 or index >= len(self._entries):
            raise IndexError(f"Index {index} is out of range for store of size {len(self._entries)}")
        return self._entries[index].message

    def search(self, query: str, top_k: int,
        policy: VectorDbOperationPolicy) -> list[MessageBase]:
        query_vector = self._embeddings.embed(query)
        operations = policy.resolve(self._entries, query_vector, top_k)
        results = self._operation_manager.apply(operations, self._entries)
        return [entry.message for entry in results]

    def __len__(self) -> int:
        return len(self._entries)
