from app.intelligence.agents import RagAgent
from app.intelligence.model import ModelConfig
from app.intelligence.agents import RagPipeline
from app.intelligence.agents import PromptManager
from app.intelligence.agents import RagPolicyFull
from app.intelligence.memory import VectorDbMemory
from app.intelligence.model import ModelEmbeddings
from app.intelligence.model import ModelFoundation
from app.intelligence.model import ModelClientBase
from app.server.config_platform import ConfigPlatform
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.tracing import TracingServiceBase

RAG_MODEL_NAMES = {
    ConfigPlatform.LOCAL: "qwen3.5:9b",
    ConfigPlatform.AWS: "eu.anthropic.claude-sonnet-5-5"
}
EMBEDDING_MODEL_NAMES = {
    ConfigPlatform.LOCAL: "qwen3-embedding:0.6b",
    ConfigPlatform.AWS: "amazon.titan-embed-text-v2:0"
}
EMBEDDING_QUERY_TEMPLATES = {
    ConfigPlatform.LOCAL: (
        "Instruct: Given a question, retrieve passages from the user's documents that answer it\n"
        "Query: {query}"
    ),
    ConfigPlatform.AWS: "{query}"
}
CONTEXT_WINDOW_TOKENS = 8192
RERANKING_MAX_OUTPUT_TOKENS = 512
ANSWER_MAX_OUTPUT_TOKENS = 8192


def build_knowledge_memory(tracing_service: TracingServiceBase, entries: list[VectorDbMemoryEntry],
    platform: ConfigPlatform, model_client: ModelClientBase) -> VectorDbMemory:
    vector_db_memory = VectorDbMemory(
        ModelEmbeddings(EMBEDDING_MODEL_NAMES[platform], tracing_service, client = model_client),
        EMBEDDING_QUERY_TEMPLATES[platform]
    )
    vector_db_memory.add_entries(entries)
    return vector_db_memory


def build_rag_agent(tracing_service: TracingServiceBase, entries: list[VectorDbMemoryEntry],
    platform: ConfigPlatform, model_client: ModelClientBase) -> RagAgent:
    vector_db_memory = build_knowledge_memory(tracing_service, entries, platform, model_client)
    model_name = RAG_MODEL_NAMES[platform]

    query_model = ModelFoundation(
        ModelConfig(model_name = model_name, temperature = 0.1, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service,
        model_client
    )
    reranking_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.1, context_window_tokens = CONTEXT_WINDOW_TOKENS,
            max_output_tokens = RERANKING_MAX_OUTPUT_TOKENS
        ),
        tracing_service,
        model_client
    )
    generation_model = ModelFoundation(
        ModelConfig(
            model_name = model_name, temperature = 0.4, context_window_tokens = CONTEXT_WINDOW_TOKENS,
            max_output_tokens = ANSWER_MAX_OUTPUT_TOKENS
        ),
        tracing_service,
        model_client
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
