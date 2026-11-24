from app.intelligence.agents import RagTopicIndex
from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorBase


class RagMetadataExtractorTopic(RagMetadataExtractorBase):
    """Gives each chunk the general topic whose vector is closest to the chunk's own,
    from a RagTopicIndex built for the model that embedded the chunks. It reuses the
    vector the chunk was indexed under, so naming the topic costs no model call.

    The similarity is kept beside the topic instead of cutting weak matches at a
    threshold: cosine scales differ between embedding models, so only a reader that
    compares chunks of one model can tell a weak match from a strong one."""

    def __init__(self, topic_index: RagTopicIndex) -> None:
        self._topic_index: RagTopicIndex = topic_index

    @property
    def metadata_type(self) -> RagMetadataType:
        return RagMetadataType.TOPIC

    def apply(self, document: RagMetadataDocument,
        metadata: list[VectorDbMemoryMetadata]) -> list[VectorDbMemoryMetadata]:
        result: list[VectorDbMemoryMetadata] = []
        for current_vector, current_metadata in zip(document.vectors, metadata):
            topic, score = self._topic_index.nearest(current_vector)
            result.append(current_metadata.model_copy(update = {"topic": topic, "topic_score": score}))
        return result
