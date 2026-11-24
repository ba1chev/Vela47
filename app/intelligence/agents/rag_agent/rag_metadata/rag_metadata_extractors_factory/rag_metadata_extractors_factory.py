from typing import Any

from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataExtractorBase
from app.intelligence.agents import RAG_METADATA_EXTRACTORS_REGISTRY
from app.intelligence.agents import RagMetadataExtractorsFactoryBase


class RagMetadataExtractorsFactory(RagMetadataExtractorsFactoryBase):
    """Concrete factory that maps each RagMetadataType to its RagMetadataExtractorBase
    subclass and delegates construction to it. Additional keyword arguments are
    forwarded verbatim, so the attacher supplies each extractor's own dependencies
    without the factory knowing which takes which.

    Registry reference:
      SECTION  -> RagMetadataExtractorSection()
      TOPIC    -> RagMetadataExtractorTopic(topic_index=<RagTopicIndex>)
      KEYWORDS -> RagMetadataExtractorKeywords(embeddings=<ModelEmbeddings>,
                  max_keywords=<int>, default 5, candidates=<int>, default 15)"""

    def create(self, type: RagMetadataType, **kwargs: Any) -> RagMetadataExtractorBase:
        cls = RAG_METADATA_EXTRACTORS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No metadata extractor class registered for type '{type}'. "
                f"Known types: {list(RAG_METADATA_EXTRACTORS_REGISTRY)}"
            )

        return cls(**kwargs)
