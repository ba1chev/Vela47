from app.intelligence.agents import RagTopicIndex
from app.server.builders import build_rag_indexer
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.builders import TOPIC_QUERY_TEMPLATES
from app.server.builders import topic_register_client
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.server.builders import TOPIC_REGISTER_AWS_REGION
from app.server.config_environment import ConfigEnvironment


class TestTopicRegisterBuilder:
    def test_every_environment_has_a_topic_query_template(self):
        assert set(TOPIC_QUERY_TEMPLATES) == set(ConfigEnvironment)
        assert all("{query}" in current for current in TOPIC_QUERY_TEMPLATES.values())

    def test_the_register_holds_a_vector_of_every_environments_embedding_model_for_every_topic(self):
        for current_environment in ConfigEnvironment:
            index = RagTopicIndex(RAG_TOPIC_REGISTER, EMBEDDING_MODEL_NAMES[current_environment])
            assert len(index) == len(RAG_TOPIC_REGISTER) and len(index._vectors[0]) == 1024

    def test_development_embeds_topics_through_ollama(self):
        assert isinstance(topic_register_client(ConfigEnvironment.DEV), ModelClientOllama)

    def test_production_embeds_topics_through_bedrock_in_its_region(self):
        client = topic_register_client(ConfigEnvironment.PROD)
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == TOPIC_REGISTER_AWS_REGION

    def test_the_indexer_names_topics_with_the_embedding_model_that_made_the_chunks(self):
        for current_environment in ConfigEnvironment:
            indexer = build_rag_indexer(current_environment, ModelClientOllama())
            topic_extractor = indexer._metadata_attacher._extractors[1]
            assert topic_extractor._topic_index.model_name == EMBEDDING_MODEL_NAMES[current_environment]
