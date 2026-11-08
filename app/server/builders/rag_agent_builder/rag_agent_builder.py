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


def build_knowledge_memory(tracing_service: TracingServiceBase,
    entries: list[VectorDbMemoryEntry]) -> VectorDbMemory:
    """One owner's documents as a searchable VectorDbMemory — the entries arrive already
    embedded from the database, and only a query is ever embedded here, with the
    instruction qwen3-embedding expects in front of a query and not in front of a
    passage. Shared by the RAG agent and the deep agent's search_documents tool, so both
    search the same way with the same model the documents were indexed with."""
    vector_db_memory = VectorDbMemory(ModelEmbeddings(EMBEDDING_MODEL_NAME, tracing_service), EMBEDDING_QUERY_TEMPLATE)
    vector_db_memory.add_entries(entries)
    return vector_db_memory


def build_rag_agent(tracing_service: TracingServiceBase,
    entries: list[VectorDbMemoryEntry]) -> RagAgent:
    """Assembles a RagAgent over one owner's documents, wired to one run's tracer —
    built per request like the DeepAgent, for the same reason: everything it holds
    reports into this run and starts from empty memory.

    The entries arrive already embedded, loaded from the database by the route, and go
    into the memory build_knowledge_memory makes, searched through HybridSearchPolicy.

    The three models differ in one setting that matters. Rewriting the query and writing
    the answer run without reasoning, which keeps them to a second or two. Reranking runs
    with it: it is the one stage that has to judge whether a passage answers a question,
    and measured on a Bulgarian question against English documents, reasoning was the
    difference between keeping the right passage and discarding every one. Every model
    gets a larger context than Ollama's default, since the answer has to fit the
    passages and the conversation at once."""
    vector_db_memory = build_knowledge_memory(tracing_service, entries)

    query_model = ModelFoundation(
        ModelConfig(model_name = RAG_MODEL_NAME, temperature = 0.1, context_window_tokens = CONTEXT_WINDOW_TOKENS),
        tracing_service
    )
    reranking_model = ModelFoundation(
        ModelConfig(model_name = RAG_MODEL_NAME, temperature = 0.1, think = True, context_window_tokens = CONTEXT_WINDOW_TOKENS),
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
