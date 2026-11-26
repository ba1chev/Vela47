from app.intelligence.agents import RagTopicIndex
from app.server.builders import build_rag_indexer
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.builders import TOPIC_QUERY_TEMPLATES
from app.server.builders import topic_register_client
from app.server.config_platform import ConfigPlatform
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.server.builders import TOPIC_REGISTER_AWS_REGION


class TestTopicRegisterBuilder:
    def test_every_platform_has_a_topic_query_template(self):
        assert set(TOPIC_QUERY_TEMPLATES) == set(ConfigPlatform)
        assert all("{query}" in current for current in TOPIC_QUERY_TEMPLATES.values())

    def test_the_register_holds_a_vector_of_every_platforms_embedding_model_for_every_topic(self):
        for current_platform in ConfigPlatform:
            index = RagTopicIndex(RAG_TOPIC_REGISTER, EMBEDDING_MODEL_NAMES[current_platform])
            assert len(index) == len(RAG_TOPIC_REGISTER) and len(index._vectors[0]) == 1024

    def test_local_embeds_topics_through_ollama(self):
        assert isinstance(topic_register_client(ConfigPlatform.LOCAL), ModelClientOllama)

    def test_aws_embeds_topics_through_bedrock_in_its_region(self):
        client = topic_register_client(ConfigPlatform.AWS)
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == TOPIC_REGISTER_AWS_REGION

    def test_the_indexer_names_topics_with_the_embedding_model_that_made_the_chunks(self):
        for current_platform in ConfigPlatform:
            indexer = build_rag_indexer(current_platform, ModelClientOllama())
            topic_extractor = indexer._metadata_attacher._extractors[1]
            assert topic_extractor._topic_index.model_name == EMBEDDING_MODEL_NAMES[current_platform]
