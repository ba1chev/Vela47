import base64
import struct
import pytest
import pathlib
import tempfile

from app.intelligence.agents import RagTopicIndex
from app.intelligence.agents import RAG_TOPIC_REGISTER
from app.intelligence.agents import decode_topic_vector
from app.intelligence.agents import encode_topic_vector
from app.intelligence.agents import RagTopicRegisterWriter
from tests.fixtures.model.fake_embeddings import FakeEmbeddings
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_INDEX
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_TEXTS
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_REGISTER
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_MODEL_NAME


def make_register(vectors):
    return {"Alpha": {"text": "alpha", "vectors": {"m": encode_topic_vector(vectors[0])}},
        "Beta": {"text": "beta", "vectors": {"m": encode_topic_vector(vectors[1])}}}


def make_path():
    return pathlib.Path(tempfile.mkdtemp()) / "register.py"


def read_register(path):
    namespace = {}
    exec(path.read_text(encoding = "utf-8"), namespace)
    return namespace["RAG_TOPIC_REGISTER"]


class TestTopicVectorCodec:
    def test_a_vector_reads_back_as_written(self):
        assert decode_topic_vector(encode_topic_vector([0.5, -1.25, 3.0])) == [0.5, -1.25, 3.0]

    def test_values_are_little_endian_float32(self):
        assert base64.b64decode(encode_topic_vector([1.0, 2.0])) == struct.pack("<2f", 1.0, 2.0)


class TestRagTopicIndex:
    def test_it_names_the_topic_nearest_a_vector_with_its_cosine(self):
        index = RagTopicIndex(make_register([[1.0, 0.0], [0.0, 1.0]]), "m")
        topic, score = index.nearest([0.2, 2.0])
        assert topic == "Beta" and score == pytest.approx(2.0 / (0.2 ** 2 + 4.0) ** 0.5)

    def test_it_knows_its_model_and_how_many_topics_it_holds(self):
        assert FAKE_TOPIC_INDEX.model_name == FAKE_TOPIC_MODEL_NAME and len(FAKE_TOPIC_INDEX) == len(FAKE_TOPIC_TEXTS)

    def test_a_register_without_vectors_of_the_model_is_refused(self):
        with pytest.raises(ValueError):
            RagTopicIndex(make_register([[1.0, 0.0], [0.0, 1.0]]), "another-model")

    def test_an_empty_register_is_refused(self):
        with pytest.raises(ValueError):
            RagTopicIndex({}, "m")

    def test_vectors_of_different_lengths_are_refused(self):
        with pytest.raises(ValueError):
            RagTopicIndex(make_register([[1.0, 0.0], [0.0, 1.0, 0.0]]), "m")

    def test_a_vector_of_another_dimension_is_refused(self):
        with pytest.raises(ValueError):
            RagTopicIndex(make_register([[1.0, 0.0], [0.0, 1.0]]), "m").nearest([1.0, 0.0, 0.0])


class TestRagTopicRegisterWriter:
    def test_every_topic_is_embedded_as_a_query_through_its_models_template(self):
        embeddings = FakeEmbeddings()
        RagTopicRegisterWriter([embeddings], {FakeEmbeddings.model_name: "Q: {query}"}, make_path()).write(FAKE_TOPIC_REGISTER)
        assert embeddings.calls == [[f"Q: {current}" for current in FAKE_TOPIC_TEXTS.values()]]

    def test_a_model_without_a_template_embeds_the_text_as_it_is(self):
        embeddings = FakeEmbeddings()
        RagTopicRegisterWriter([embeddings], path = make_path()).write(FAKE_TOPIC_REGISTER)
        assert embeddings.calls == [list(FAKE_TOPIC_TEXTS.values())]

    def test_the_written_file_reads_back_as_the_register_it_returned(self):
        path = make_path()
        written = RagTopicRegisterWriter([FakeEmbeddings()], path = path).write(make_register([[1.0, 0.0], [0.0, 1.0]]))
        assert read_register(path) == written
        assert decode_topic_vector(written["Alpha"]["vectors"][FakeEmbeddings.model_name]) == FakeEmbeddings().embed("alpha")

    def test_vectors_of_models_that_were_not_given_are_kept(self):
        register = make_register([[1.0, 0.0], [0.0, 1.0]])
        written = RagTopicRegisterWriter([FakeEmbeddings()], path = make_path()).write(register)
        assert written["Beta"]["vectors"]["m"] == register["Beta"]["vectors"]["m"]
        assert set(written["Beta"]["vectors"]) == {"m", FakeEmbeddings.model_name}

    def test_a_topic_without_vectors_reads_back_without_vectors(self):
        path = make_path()
        RagTopicRegisterWriter([], path = path).write({"Alpha": {"text": "alpha", "vectors": {}}})
        assert read_register(path) == {"Alpha": {"text": "alpha", "vectors": {}}}


class TestRagTopicRegister:
    def test_it_holds_a_hundred_topics_each_with_a_text(self):
        assert len(RAG_TOPIC_REGISTER) == 100
        assert all(current["text"].startswith(current_topic.split()[0]) for current_topic, current in RAG_TOPIC_REGISTER.items())

    def test_the_file_is_exactly_what_the_writer_writes(self):
        rendered = RagTopicRegisterWriter([])._render(RAG_TOPIC_REGISTER)
        assert rendered == RagTopicRegisterWriter.REGISTER_PATH.read_text(encoding = "utf-8")
