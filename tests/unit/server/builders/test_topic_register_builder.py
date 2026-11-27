from app.intelligence.agents import RagTopicIndex
from app.server.builders import build_rag_indexer
from app.intelligence.model import ModelClientType
from app.intelligence.model import ModelClientOllama
from app.intelligence.model import ModelClientBedrock
from app.server.builders import EMBEDDING_MODEL_NAMES
from app.server.builders import TOPIC_QUERY_TEMPLATES
from app.server.builders import topic_register_client
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.server.builders import TOPIC_REGISTER_AWS_REGION


class TestTopicRegisterBuilder:
    def test_every_backend_has_a_topic_query_template(self):
        assert set(TOPIC_QUERY_TEMPLATES) == set(ModelClientType)
        assert all("{query}" in current for current in TOPIC_QUERY_TEMPLATES.values())

    def test_the_register_holds_a_vector_of_every_backends_embedding_model_for_every_topic(self):
        for current_type in ModelClientType:
            index = RagTopicIndex(RAG_TOPIC_REGISTER, EMBEDDING_MODEL_NAMES[current_type])
            assert len(index) == len(RAG_TOPIC_REGISTER) and len(index._vectors[0]) == 1024

    def test_ollama_embeds_topics_through_the_local_server(self):
        assert isinstance(topic_register_client(ModelClientType.OLLAMA), ModelClientOllama)

    def test_bedrock_embeds_topics_in_the_region_of_aws(self):
        client = topic_register_client(ModelClientType.BEDROCK)
        assert isinstance(client, ModelClientBedrock) and client._runtime.meta.region_name == TOPIC_REGISTER_AWS_REGION

    def test_the_indexer_names_topics_with_the_embedding_model_that_made_the_chunks(self):
        for current_client in (ModelClientOllama(), ModelClientBedrock(TOPIC_REGISTER_AWS_REGION)):
            indexer = build_rag_indexer(current_client)
            topic_extractor = indexer._metadata_attacher._extractors[1]
            assert topic_extractor._topic_index.model_name == EMBEDDING_MODEL_NAMES[current_client.client_type]
