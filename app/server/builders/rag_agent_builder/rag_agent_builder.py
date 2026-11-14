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
from app.server.config_environment import ConfigEnvironment

RAG_MODEL_NAMES = {
    ConfigEnvironment.DEV: "qwen3.5:9b",
    ConfigEnvironment.PROD: "qwen3.5:35b-a3b"
}
EMBEDDING_MODEL_NAMES = {
    ConfigEnvironment.DEV: "qwen3-embedding:0.6b",
    ConfigEnvironment.PROD: "qwen3-embedding:8b"
}
EMBEDDING_QUERY_TEMPLATE = (
    "Instruct: Given a question, retrieve passages from the user's documents that answer it\n"
    "Query: {query}"
)
CONTEXT_WINDOW_TOKENS = {
    ConfigEnvironment.DEV: 8192,
    ConfigEnvironment.PROD: 32768
}
KEEP_ALIVE = {
    ConfigEnvironment.DEV: "30m",
    ConfigEnvironment.PROD: "-1"
}
RERANKING_MAX_OUTPUT_TOKENS = 512


def build_knowledge_memory(tracing_service: TracingServiceBase, entries: list[VectorDbMemoryEntry],
    environment: ConfigEnvironment) -> VectorDbMemory:
    vector_db_memory = VectorDbMemory(
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[environment], tracing_service, KEEP_ALIVE[environment]),
        EMBEDDING_QUERY_TEMPLATE
    )
    vector_db_memory.add_entries(entries)
    return vector_db_memory


def build_rag_agent(tracing_service: TracingServiceBase, entries: list[VectorDbMemoryEntry],
    environment: ConfigEnvironment) -> RagAgent:
    vector_db_memory = build_knowledge_memory(tracing_service, entries, environment)
    model_name = RAG_MODEL_NAMES[environment]
    context_window_tokens = CONTEXT_WINDOW_TOKENS[environment]
    keep_alive = KEEP_ALIVE[environment]

    query_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.1,
            context_window_tokens = context_window_tokens, keep_alive = keep_alive
        ),
        tracing_service
    )
    reranking_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.1,
            context_window_tokens = context_window_tokens, keep_alive = keep_alive,
            max_output_tokens = RERANKING_MAX_OUTPUT_TOKENS
        ),
        tracing_service
    )
    generation_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.4,
            context_window_tokens = context_window_tokens, keep_alive = keep_alive
        ),
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
