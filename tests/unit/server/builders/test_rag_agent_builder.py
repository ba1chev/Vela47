import re
import pathlib

from app.server.builders import KEEP_ALIVE
from app.server.builders import MODEL_NAMES
from app.server.builders import RAG_MODEL_NAMES
from app.server.builders import build_rag_agent
from app.server.builders import build_rag_indexer
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.builders import CONTEXT_WINDOW_TOKENS
from app.server.builders import build_knowledge_memory
from app.intelligence.tracing import TracingServiceNull
from app.server.config_environment import ConfigEnvironment

PROD_VARIABLES = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "prod" / "variables.tf"


def prod_pulled_models():
    block = re.search(r'variable "ollama_models" \{.*?default\s*=\s*\[(.*?)\]', PROD_VARIABLES.read_text(), re.DOTALL)
    return set(re.findall(r'"([^"]+)"', block.group(1)))


class TestRagAgentBuilder:
    def test_every_environment_has_its_models_and_context_window(self):
        for current in (RAG_MODEL_NAMES, EMBEDDING_MODEL_NAMES, CONTEXT_WINDOW_TOKENS, KEEP_ALIVE):
            assert set(current) == set(ConfigEnvironment)

    def test_both_agents_share_one_model_per_environment(self):
        """One language model on the GPU, so Ollama never swaps models between requests."""
        for current_environment in ConfigEnvironment:
            assert RAG_MODEL_NAMES[current_environment] == MODEL_NAMES[current_environment]

    def test_prod_reads_at_least_as_much_as_dev(self):
        assert CONTEXT_WINDOW_TOKENS[ConfigEnvironment.PROD] >= CONTEXT_WINDOW_TOKENS[ConfigEnvironment.DEV]

    def test_prod_keeps_its_models_loaded(self):
        """A request after a quiet hour must not wait for 22 GB to load from disk again."""
        assert KEEP_ALIVE[ConfigEnvironment.PROD] == "-1"

    def test_prod_pulls_every_model_the_prod_server_asks_for(self):
        prod = ConfigEnvironment.PROD
        assert prod_pulled_models() == {MODEL_NAMES[prod], RAG_MODEL_NAMES[prod], EMBEDDING_MODEL_NAMES[prod]}

    def test_the_rag_agent_runs_on_the_models_of_its_environment(self):
        for current_environment in ConfigEnvironment:
            agent = build_rag_agent(TracingServiceNull(), [], current_environment)
            assert agent._model._config.model_name == RAG_MODEL_NAMES[current_environment]
            assert agent._model._config.context_window_tokens == CONTEXT_WINDOW_TOKENS[current_environment]
            assert agent._model._config.keep_alive == KEEP_ALIVE[current_environment]
            assert agent._vector_db_memory._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_environment]
            assert agent._vector_db_memory._embeddings._keep_alive == KEEP_ALIVE[current_environment]

    def test_documents_are_searched_with_the_embedding_model_they_were_indexed_with(self):
        for current_environment in ConfigEnvironment:
            memory = build_knowledge_memory(TracingServiceNull(), [], current_environment)
            indexer = build_rag_indexer(current_environment)
            assert memory._embeddings.model_name == indexer._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_environment]
