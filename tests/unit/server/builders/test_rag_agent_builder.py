import re
import pathlib

from app.server.builders import MODEL_NAMES
from app.server.builders import RAG_MODEL_NAMES
from app.server.builders import build_rag_agent
from app.server.builders import build_rag_indexer
from app.intelligence.model import ModelClientOllama
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.config_platform import ConfigPlatform
from app.server.builders import build_knowledge_memory
from app.intelligence.tracing import TracingServiceNull
from app.server.builders import ANSWER_MAX_OUTPUT_TOKENS
from app.server.builders import EMBEDDING_QUERY_TEMPLATES

ENVIRONMENTS = pathlib.Path(__file__).resolve().parents[4] / "deploy" / "terraform" / "environments"
AWS_ENVIRONMENTS = ("dev", "staging", "prod")


def allowed_models(environment):
    variables = (ENVIRONMENTS / environment / "app" / "variables.tf").read_text()
    block = re.search(r'variable "bedrock_model_ids" \{.*?default\s*=\s*\[(.*?)\]', variables, re.DOTALL)
    return set(re.findall(r'"([^"]+)"', block.group(1)))


class TestRagAgentBuilder:
    def test_every_platform_has_its_models_and_query_template(self):
        for current in (RAG_MODEL_NAMES, EMBEDDING_MODEL_NAMES, EMBEDDING_QUERY_TEMPLATES):
            assert set(current) == set(ConfigPlatform)
        assert all("{query}" in current for current in EMBEDDING_QUERY_TEMPLATES.values())

    def test_both_agents_share_one_model_per_platform(self):
        for current_platform in ConfigPlatform:
            assert RAG_MODEL_NAMES[current_platform] == MODEL_NAMES[current_platform]

    def test_every_aws_environment_may_call_exactly_the_models_its_server_asks_for(self):
        aws = ConfigPlatform.AWS
        for current_environment in AWS_ENVIRONMENTS:
            assert allowed_models(current_environment) == {MODEL_NAMES[aws], RAG_MODEL_NAMES[aws], EMBEDDING_MODEL_NAMES[aws]}

    def test_the_rag_agent_runs_on_the_models_and_the_client_it_is_given(self):
        client = ModelClientOllama()
        for current_platform in ConfigPlatform:
            agent = build_rag_agent(TracingServiceNull(), [], current_platform, client)
            assert agent._model._config.model_name == RAG_MODEL_NAMES[current_platform] and agent._model._client is client
            assert agent._vector_db_memory._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_platform]
            assert agent._vector_db_memory._embeddings._client is client
            assert agent._vector_db_memory._query_template == EMBEDDING_QUERY_TEMPLATES[current_platform]

    def test_documents_are_searched_with_the_embedding_model_they_were_indexed_with(self):
        client = ModelClientOllama()
        for current_platform in ConfigPlatform:
            memory = build_knowledge_memory(TracingServiceNull(), [], current_platform, client)
            indexer = build_rag_indexer(current_platform, client)
            assert memory._embeddings.model_name == indexer._embeddings.model_name == EMBEDDING_MODEL_NAMES[current_platform]
            assert indexer._embeddings._client is client

    def test_the_answer_has_room_for_a_long_reply(self):
        agent = build_rag_agent(TracingServiceNull(), [], ConfigPlatform.LOCAL, ModelClientOllama())
        assert agent._model._config.max_output_tokens == ANSWER_MAX_OUTPUT_TOKENS
