# A topic register embedded with FakeEmbeddings: three topics whose texts share words with
# the documents the tests index, so the nearest topic of every chunk is known in advance.

from app.intelligence.agents import RagTopicIndex
from app.intelligence.agents import encode_topic_vector
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

FAKE_TOPIC_MODEL_NAME = FakeEmbeddings.model_name

FAKE_TOPIC_TEXTS = {
    "Errors": "Error codes, a secret that could not be read, and how to fix them.",
    "Backups": "Backups of the database, how often they run and how many days they are kept.",
    "Office": "The office, the coffee machine and when it is cleaned on Fridays."
}

FAKE_TOPIC_REGISTER = {
    current_topic: {
        "text": current_text,
        "vectors": {FAKE_TOPIC_MODEL_NAME: encode_topic_vector(FakeEmbeddings().embed(current_text))}
    }
    for current_topic, current_text in FAKE_TOPIC_TEXTS.items()
}

FAKE_TOPIC_INDEX = RagTopicIndex(FAKE_TOPIC_REGISTER, FAKE_TOPIC_MODEL_NAME)
