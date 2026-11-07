from app.intelligence.memory import VectorDbMemory
from app.intelligence.messages import MessageSystem
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.memory import VectorDbMemoryEntry
from app.intelligence.memory import SemanticSearchPolicy
from tests.fixtures.model.fake_embeddings import FakeEmbeddings


def make_entries(embeddings, *texts):
    return [
        VectorDbMemoryEntry(message = MessageSystem(content = current_text), vector = embeddings.embed(current_text))
        for current_text in texts
    ]


class TestVectorDbMemory:
    def test_added_entries_are_not_embedded_again(self):
        embeddings = FakeEmbeddings()
        entries = make_entries(embeddings, "alpha", "beta")
        embeddings.calls.clear()
        memory = VectorDbMemory(embeddings)
        memory.add_entries(entries)
        assert len(memory) == 2 and embeddings.calls == []

    def test_an_empty_memory_finds_nothing_and_embeds_nothing(self):
        embeddings = FakeEmbeddings()
        assert VectorDbMemory(embeddings).search_entries("anything", 3, SemanticSearchPolicy()) == []
        assert embeddings.calls == []

    def test_search_entries_returns_entries_with_their_vectors(self):
        embeddings = FakeEmbeddings()
        memory = VectorDbMemory(embeddings)
        memory.add_entries(make_entries(embeddings, "deploy script", "coffee machine"))
        found = memory.search_entries("deploy", 1, SemanticSearchPolicy())
        assert found[0].message.content == "deploy script" and found[0].vector

    def test_search_returns_the_messages(self):
        embeddings = FakeEmbeddings()
        memory = VectorDbMemory(embeddings)
        memory.add_entries(make_entries(embeddings, "deploy script"))
        assert memory.search("deploy", 1, SemanticSearchPolicy())[0].content == "deploy script"

    def test_only_the_query_vector_uses_the_template(self):
        embeddings = FakeEmbeddings()
        memory = VectorDbMemory(embeddings, "Instruct: find it\nQuery: {query}")
        memory.add_entries(make_entries(embeddings, "deploy script", "find instruct query"))
        embeddings.calls.clear()
        found = memory.search_entries("deploy", 2, HybridSearchPolicy())
        assert embeddings.calls == [["Instruct: find it\nQuery: deploy"]]
        assert found[0].message.content == "deploy script"
