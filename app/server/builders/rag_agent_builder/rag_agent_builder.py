from app.intelligence.agents import RagAgent
from app.intelligence.model import ModelConfig
from app.intelligence.agents import RagPipeline
from app.intelligence.agents import PromptManager
from app.intelligence.agents import RagPolicyFull
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelFoundation
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.tracing import TracingServiceBase

RAG_MODEL_NAME = "qwen3.5:9b"
EMBEDDING_MODEL_NAME = "qwen3-embedding:0.6b"
EMBEDDING_QUERY_TEMPLATE = (
    "Instruct: Given a question, retrieve passages from the user's documents that answer it\n"
    "Query: {query}"
)
CONTEXT_WINDOW_TOKENS = 8192
RERANKING_MAX_OUTPUT_TOKENS = 512


def build_knowledge_memory(tracing_service: TracingServiceBase,
    entries: list[VectorDbMemoryEntry]) -> VectorDbMemory:
    vector_db_memory = VectorDbMemory(ModelEmbeddings(EMBEDDING_MODEL_NAME, tracing_service), EMBEDDING_QUERY_TEMPLATE)
    vector_db_memory.add_entries(entries)
    return vector_db_memory


def build_rag_agent(tracing_service: TracingServiceBase,
    entries: list[VectorDbMemoryEntry]) -> RagAgent:
    vector_db_memory = build_knowledge_memory(tracing_service, entries)

    query_model = ModelFoundation(
        ModelConfig(model_name = RAG_MODEL_NAME, temperature = 0.1, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service
    )
    reranking_model = ModelFoundation(
        ModelConfig(
            model_name = RAG_MODEL_NAME, temperature = 0.1, context_window_tokens = CONTEXT_WINDOW_TOKENS,
            max_output_tokens = RERANKING_MAX_OUTPUT_TOKENS
        ),
        tracing_service
    )
    generation_model = ModelFoundation(
        ModelConfig(model_name = RAG_MODEL_NAME, temperature = 0.4, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service
    )

    policy = RagPolicyFull(
        query_model = query_model,
        reranking_model = reranking_model,
        generation_model = generation_model,
        vector_db_memory = vector_db_memory,
        retrieval_policy = HybridSearchPolicy(),
        tracing_service = tracing_service
    )

    return RagAgent(
        model = generation_model,
        prompt_manager = PromptManager(),
        max_context_window_size = 6,
        rag_pipeline = RagPipeline(policy, tracing_service),
        vector_db_memory = vector_db_memory,
        tracing_service = tracing_service
    )
