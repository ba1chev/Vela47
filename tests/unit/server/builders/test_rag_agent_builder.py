import re
import pathlib

from app.server.builders import MODEL_NAMES
from app.server.builders import RAG_MODEL_NAMES
from app.server.builders import build_rag_agent
from app.server.builders import build_rag_indexer
from app.intelligence.model import ModelClientOllama
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.builders import build_knowledge_memory
from app.intelligence.tracing import TracingServiceNull
from app.server.builders import EMBEDDING_QUERY_TEMPLATES
from app.server.config_environment import ConfigEnvironment

PROD_VARIABLES = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "prod" / "variables.tf"


def prod_allowed_models():
    block = re.search(r'variable "bedrock_model_ids" \{.*?default\s*=\s*\[(.*?)\]', PROD_VARIABLES.read_text(), re.DOTALL)
    return set(re.findall(r'"([^"]+)"', block.group(1)))


class TestRagAgentBuilder:
    def test_every_environment_has_its_models_and_query_template(self):
        for current in (RAG_MODEL_NAMES, EMBEDDING_MODEL_NAMES, EMBEDDING_QUERY_TEMPLATES):
            assert set(current) == set(ConfigEnvironment)
        assert all("{query}" in current for current in EMBEDDING_QUERY_TEMPLATES.values())

    def test_both_agents_share_one_model_per_environment(self):
        for current_environment in ConfigEnvironment:
            assert RAG_MODEL_NAMES[current_environment] == MODEL_NAMES[current_environment]

    def test_prod_may_call_exactly_the_models_the_prod_server_asks_for(self):
        prod = ConfigEnvironment.PROD
        assert prod_allowed_models() == {MODEL_NAMES[prod], RAG_MODEL_NAMES[prod], EMBEDDING_MODEL_NAMES[prod]}

    def test_the_rag_agent_runs_on_the_models_and_the_client_it_is_given(self):
        client = ModelClientOllama()
        for current_environment in ConfigEnvironment:
            agent = build_rag_agent(TracingServiceNull(), [], current_environment, client)
            assert agent._model._config.model_name == RAG_MODEL_NAMES[current_environment] and agent._model._client is client
            assert agent._vector_db_memory._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_environment]
            assert agent._vector_db_memory._embeddings._client is client
            assert agent._vector_db_memory._query_template == EMBEDDING_QUERY_TEMPLATES[current_environment]

    def test_documents_are_searched_with_the_embedding_model_they_were_indexed_with(self):
        client = ModelClientOllama()
        for current_environment in ConfigEnvironment:
            memory = build_knowledge_memory(TracingServiceNull(), [], current_environment, client)
            indexer = build_rag_indexer(current_environment, client)
            assert memory._embeddings.model_name == indexer._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_environment]
            assert indexer._embeddings._client is client
