import json
import pytest

from app.intelligence.agents import RagAgent
from app.intelligence.agents import RagIndexer
from app.intelligence.messages import MessageAI
from app.intelligence.agents import RagPipeline
from app.intelligence.agents import RagLayerType
from app.intelligence.agents import PromptManager
from app.intelligence.agents import RagPolicyFull
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import RagLayersFactory
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.agents import RAG_LAYERS_REGISTRY
from app.intelligence.agents import RagChunkerRecursive
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

TEXT = "Error E1042 means the RDS secret could not be read.\n\nBackups are kept for 14 days."


def make_agent(model, tracer = None):
    embeddings = FakeEmbeddings()
    memory = VectorDbMemory(embeddings)
    memory.add_entries(RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), embeddings).index("d1", "guide.md", TEXT))
    policy = RagPolicyFull(model, model, model, memory, HybridSearchPolicy(), tracer)
    return RagAgent(model, PromptManager(), 6, RagPipeline(policy, tracer), memory, tracer)


def scores(*pairs):
    return json.dumps([{"index": index, "score": score} for index, score in pairs])


class TestRagLayersFactory:
    def test_every_layer_type_is_registered(self):
        assert set(RAG_LAYERS_REGISTRY) == set(RagLayerType)

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagLayersFactory().create("summarize")


class TestRagPipeline:
    def test_the_full_policy_runs_four_layers(self):
        assert len(RagPipeline(RagPolicyFull(FakeModel(), FakeModel(), FakeModel(), VectorDbMemory(FakeEmbeddings()), HybridSearchPolicy()))) == 4

    def test_every_layer_is_traced_by_name_with_what_it_produced(self):
        tracer = TracingService()
        make_agent(FakeModel([scores((1, 9), (2, 1)), "It means the secret could not be read. [1]"]), tracer).execute(
            MessageHuman(content = "What does E1042 mean?")
        )
        finished = {current.label: current.payload for current in tracer.events() if current.type is TraceEventType.LAYER_FINISHED}
        assert list(finished) == ["Query", "Retrieval", "Reranking", "Generation"]
        assert finished["Retrieval"]["candidates"] == 2 and finished["Reranking"]["passages"] == 1
        assert finished["Reranking"]["reranked"] is True


class TestRagAgent:
    def test_it_answers_with_its_sources(self):
        reply = make_agent(FakeModel([scores((1, 9), (2, 1)), "It means the secret could not be read. [1]"])).execute(
            MessageHuman(content = "What does E1042 mean?")
        )
        assert reply.content.strip().endswith("[1]")
        assert reply.response_metadata["sources"][0]["excerpt"].startswith("Error E1042")

    def test_a_follow_up_is_rewritten_using_the_earlier_turns(self):
        model = FakeModel([scores((1, 9)), "first answer", "How do I fix error E1042?", scores((1, 9)), "second answer"])
        agent = make_agent(model)
        agent.execute(MessageHuman(content = "What does E1042 mean?"))
        agent.execute(MessageHuman(content = "How do I fix it?"))
        transcript = model.calls[2][0][1].content
        assert "User: What does E1042 mean?" in transcript and "Assistant: first answer" in transcript

    def test_a_restored_conversation_is_history_for_the_next_question(self):
        model = FakeModel(["standalone", scores((1, 9)), "answer"])
        agent = make_agent(model)
        agent.restore([MessageHuman(content = "earlier"), MessageAI(content = "reply")])
        agent.execute(MessageHuman(content = "now?"))
        assert "User: earlier" in model.calls[0][0][1].content
