from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataExtractorBase
from app.intelligence.agents import RagMetadataExtractorTopic
from app.intelligence.agents import RagMetadataExtractorSection
from app.intelligence.agents import RagMetadataExtractorKeywords


RAG_METADATA_EXTRACTORS_REGISTRY: dict[RagMetadataType, type[RagMetadataExtractorBase]] = {
    RagMetadataType.SECTION: RagMetadataExtractorSection,
    RagMetadataType.TOPIC: RagMetadataExtractorTopic,
    RagMetadataType.KEYWORDS: RagMetadataExtractorKeywords
}
