import json

from app.intelligence.agents import RagContext
from app.intelligence.agents import RagIndexer
from app.intelligence.messages import MessageAI
from app.intelligence.agents import RagLayerType
from app.intelligence.agents import RagQueryLayer
from app.intelligence.messages import MessageType
from app.intelligence.messages import MessageHuman
from app.intelligence.memory import VectorDbMemory
from app.intelligence.tracing import TracingService
from app.intelligence.tracing import TraceEventType
from app.intelligence.agents import RagRetrievalLayer
from app.intelligence.agents import RagRerankingLayer
from tests.fixtures.model.fake_model import FakeModel
from app.intelligence.agents import RagGenerationLayer
from app.intelligence.memory import HybridSearchPolicy
from app.intelligence.agents import RagChunkerRecursive
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

TEXT = "Error E1042 means the RDS secret could not be read.\n\nBackups are kept for 14 days.\n\nThe coffee machine is cleaned on Fridays."


def make_entries():
    return RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), FakeEmbeddings()).index("d1", "guide.md", TEXT)


def make_context(goal = "What does E1042 mean?", **fields):
    return RagContext(goal = MessageHuman(content = goal), **fields)


HISTORY = [MessageHuman(content = "What does E1042 mean?"), MessageAI(content = "It means the secret could not be read.")]


class TestRagQueryLayer:
    def test_its_type_is_query(self):
        assert RagQueryLayer(FakeModel()).layer_type is RagLayerType.QUERY

    def test_without_history_the_question_is_the_query_and_no_model_is_called(self):
        model = FakeModel()
        context = make_context()
        RagQueryLayer(model).execute(context)
        assert context.query == "What does E1042 mean?" and model.calls == []

    def test_with_history_the_model_rewrites_the_question(self):
        context = make_context("How do I fix it?", history = HISTORY)
        RagQueryLayer(FakeModel(["How do I fix error E1042?"])).execute(context)
        assert context.query == "How do I fix error E1042?"

    def test_history_reaches_the_model_as_one_transcript_not_as_turns(self):
        model = FakeModel(["How do I fix error E1042?"])
        RagQueryLayer(model).execute(make_context("How do I fix it?", history = HISTORY))
        messages = model.calls[0][0]
        assert [current.type for current in messages] == [MessageType.SYSTEM_MESSAGE, MessageType.HUMAN_MESSAGE]
        assert "User: What does E1042 mean?" in messages[1].content and "LATEST MESSAGE: How do I fix it?" in messages[1].content

    def test_a_reply_far_longer_than_the_question_is_taken_for_an_answer_and_dropped(self):
        context = make_context("How do I fix it?", history = HISTORY)
        RagQueryLayer(FakeModel(["To fix it, " + "do this and that " * 30])).execute(context)
        assert context.query == "How do I fix it?"

    def test_an_empty_reply_falls_back_to_the_question(self):
        context = make_context("How do I fix it?", history = HISTORY)
        RagQueryLayer(FakeModel(["   "])).execute(context)
        assert context.query == "How do I fix it?"


class TestRagRetrievalLayer:
    def make_layer(self, embeddings, entries, candidates = 12):
        memory = VectorDbMemory(embeddings)
        memory.add_entries(entries)
        return RagRetrievalLayer(memory, HybridSearchPolicy(), candidates)

    def test_its_type_is_retrieval(self):
        assert self.make_layer(FakeEmbeddings(), []).layer_type is RagLayerType.RETRIEVAL

    def test_the_matching_passage_comes_first(self):
        context = make_context(query = "What does E1042 mean?")
        self.make_layer(FakeEmbeddings(), make_entries()).execute(context)
        assert "E1042" in context.candidates[0].message.content

    def test_it_searches_for_both_the_question_and_its_rewrite(self):
        embeddings = FakeEmbeddings()
        layer = self.make_layer(embeddings, make_entries())
        embeddings.calls.clear()
        layer.execute(make_context("How do I fix it?", query = "How do I fix error E1042?"))
        assert embeddings.calls == [["How do I fix it?"], ["How do I fix error E1042?"]]

    def test_a_rewrite_equal_to_the_question_is_searched_once(self):
        embeddings = FakeEmbeddings()
        layer = self.make_layer(embeddings, make_entries())
        embeddings.calls.clear()
        layer.execute(make_context(query = "What does E1042 mean?"))
        assert len(embeddings.calls) == 1

    def test_a_bad_rewrite_cannot_lose_what_the_question_finds(self):
        context = make_context("What does E1042 mean?", query = "one_line_no_explanation")
        self.make_layer(FakeEmbeddings(), make_entries()).execute(context)
        assert "E1042" in context.candidates[0].message.content

    def test_the_number_of_candidates_is_capped(self):
        context = make_context(query = "the")
        self.make_layer(FakeEmbeddings(), make_entries(), candidates = 1).execute(context)
        assert len(context.candidates) == 1

    def test_no_documents_means_no_candidates(self):
        context = make_context()
        self.make_layer(FakeEmbeddings(), []).execute(context)
        assert context.candidates == []


class TestRagRerankingLayer:
    def scores(self, *pairs):
        return json.dumps([{"index": index, "score": score} for index, score in pairs])

    def test_its_type_is_reranking(self):
        assert RagRerankingLayer(FakeModel()).layer_type is RagLayerType.RERANKING

    def test_candidates_are_reordered_by_score_and_weak_ones_dropped(self):
        entries = make_entries()
        context = make_context(query = "q", candidates = entries)
        RagRerankingLayer(FakeModel([self.scores((1, 2), (2, 9), (3, 6))]), top_n = 4, min_score = 4).execute(context)
        assert [current.message.id for current in context.passages] == ["d1-1", "d1-2"]
        assert context.relevance == {"d1-0": 2, "d1-1": 9, "d1-2": 6}

    def test_top_n_caps_the_passages(self):
        context = make_context(query = "q", candidates = make_entries())
        RagRerankingLayer(FakeModel([self.scores((1, 9), (2, 9), (3, 9))]), top_n = 2).execute(context)
        assert len(context.passages) == 2

    def test_an_unparsable_reply_keeps_retrieval_order_and_marks_it_unranked(self):
        entries = make_entries()
        context = make_context(query = "q", candidates = entries)
        RagRerankingLayer(FakeModel(["I think passage two is best."]), top_n = 2).execute(context)
        assert context.passages == entries[:2] and context.relevance == {}

    def test_the_reply_is_constrained_to_one_score_per_candidate(self):
        context = make_context(candidates = make_entries())
        model = FakeModel([self.scores((1, 9), (2, 9), (3, 9))])
        RagRerankingLayer(model).execute(context)
        schema = model.output_schemas[0]
        assert schema["minItems"] == schema["maxItems"] == len(context.candidates)

    def test_no_candidates_costs_no_model_call(self):
        model = FakeModel()
        context = make_context(candidates = [])
        RagRerankingLayer(model).execute(context)
        assert model.calls == [] and context.passages == []

    def test_the_resolved_rewrite_is_shown_beside_the_question(self):
        model = FakeModel([self.scores((1, 9))])
        RagRerankingLayer(model).execute(make_context("How do I fix it?", query = "How do I fix E1042?", candidates = make_entries()[:1]))
        report = model.calls[0][0][1].content
        assert "QUERY: How do I fix it?" in report and "How do I fix E1042?" in report


class TestRagGenerationLayer:
    def test_its_type_is_generation(self):
        assert RagGenerationLayer(FakeModel()).layer_type is RagLayerType.GENERATION

    def test_passages_reach_the_model_numbered_with_their_titles(self):
        model = FakeModel(["answer"])
        RagGenerationLayer(model).execute(make_context(passages = make_entries()[:2]))
        prompt = model.calls[0][0][-1].content
        assert "[1] guide.md\nError E1042" in prompt and "[2] guide.md\nBackups" in prompt

    def test_the_question_comes_after_the_sources(self):
        model = FakeModel(["answer"])
        RagGenerationLayer(model).execute(make_context(passages = make_entries()[:2]))
        prompt = model.calls[0][0][-1].content
        assert prompt.startswith("SOURCES:") and prompt.rstrip().endswith("QUESTION: What does E1042 mean?")

    def test_the_answer_carries_its_sources_by_the_same_numbers(self):
        entries = make_entries()
        context = make_context(passages = [entries[1], entries[0]], relevance = {"d1-1": 9})
        RagGenerationLayer(FakeModel(["answer"])).execute(context)
        sources = context.final.response_metadata["sources"]
        assert [(current["index"], current["chunk_index"], current["score"]) for current in sources] == [(1, 1, 9), (2, 0, None)]
        assert sources[0]["title"] == "guide.md" and sources[0]["document_id"] == "d1"

    def test_history_comes_before_the_question(self):
        model = FakeModel(["answer"])
        RagGenerationLayer(model).execute(make_context(history = HISTORY, passages = make_entries()[:1]))
        assert [current.content for current in model.calls[0][0][1:3]] == [HISTORY[0].content, HISTORY[1].content]

    def test_without_passages_the_question_only_appears_quoted_in_an_instruction(self):
        model = FakeModel(["Your documents do not cover it."])
        context = make_context("What is the capital of France?", history = HISTORY, passages = [])
        RagGenerationLayer(model).execute(context)
        messages = model.calls[0][0]
        assert len(messages) == 1 and messages[0].type is MessageType.HUMAN_MESSAGE
        assert "«What is the capital of France?»" in messages[0].content
        assert context.final.response_metadata["sources"] == []

    def test_every_chunk_is_reported_as_it_streams(self):
        tracer = TracingService()
        RagGenerationLayer(FakeModel(["one two three"]), tracer).execute(make_context(passages = make_entries()[:1]))
        assert len([current for current in tracer.events() if current.type is TraceEventType.ANSWER_CHUNK]) == 3
