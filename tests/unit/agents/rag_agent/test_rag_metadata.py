import pytest

from app.intelligence.agents import RagMetadataType
from app.intelligence.agents import RagMetadataDocument
from app.intelligence.agents import RagMetadataAttacher
from app.intelligence.memory import VectorDbMemorySource
from app.intelligence.memory import VectorDbMemoryMetadata
from app.intelligence.agents import RagMetadataExtractorTopic
from tests.fixtures.model.fake_embeddings import FakeEmbeddings
from app.intelligence.agents import RagMetadataExtractorSection
from app.intelligence.agents import RagMetadataExtractorKeywords
from app.intelligence.agents import RagMetadataExtractorsFactory
from app.intelligence.agents import RAG_METADATA_EXTRACTORS_REGISTRY
from tests.fixtures.agents.fake_topic_register import FAKE_TOPIC_INDEX

RUNBOOK = (
    "# Runbook\n\nThis runbook is for the on-call engineer.\n\n"
    "## Errors\nError E1042 means the secret could not be read.\n\n"
    "### Fixes\nRestart the service after the rotation.\n\n"
    "## Backups\nBackups are kept for 14 days."
)


def make_document(text, chunks):
    return RagMetadataDocument(
        document_id = "d1", title = "guide.md", text = text, chunks = chunks, vectors = FakeEmbeddings().embed_many(chunks)
    )


def make_metadata(document):
    metadata = []
    for index, current_chunk in enumerate(document.chunks):
        start = document.text.find(current_chunk)
        span = {"start": start, "end": start + len(current_chunk)} if start >= 0 else {}
        metadata.append(VectorDbMemoryMetadata(
            source = VectorDbMemorySource(document_id = "d1", title = "guide.md", chunk_index = index, **span)
        ))
    return metadata


def sections(text, chunks):
    document = make_document(text, chunks)
    return [current.section for current in RagMetadataExtractorSection().apply(document, make_metadata(document))]


def keywords(text, chunks, embeddings = None, **kwargs):
    document = make_document(text, chunks)
    extractor = RagMetadataExtractorKeywords(embeddings or FakeEmbeddings(), **kwargs)
    return [current.keywords for current in extractor.apply(document, make_metadata(document))]


class TestRagMetadataDocument:
    def test_every_chunk_needs_exactly_one_vector(self):
        with pytest.raises(ValueError):
            RagMetadataDocument(document_id = "d1", title = "t", text = "a b", chunks = ["a", "b"], vectors = [[1.0]])


class TestRagMetadataExtractorSection:
    def test_its_type_is_section(self):
        assert RagMetadataExtractorSection().metadata_type is RagMetadataType.SECTION

    def test_a_chunk_is_named_by_the_path_of_the_headings_above_it(self):
        chunks = ["Error E1042 means the secret could not be read.", "Restart the service after the rotation."]
        assert sections(RUNBOOK, chunks) == ["Runbook › Errors", "Runbook › Errors › Fixes"]

    def test_a_heading_closes_the_headings_of_its_own_level_and_deeper(self):
        assert sections(RUNBOOK, ["Backups are kept for 14 days."]) == ["Runbook › Backups"]

    def test_a_chunk_that_opens_with_headings_belongs_to_the_last_of_them(self):
        assert sections(RUNBOOK, ["## Backups\nBackups are kept for 14 days."]) == ["Runbook › Backups"]
        assert sections("# Runbook\n\n## Backups\nKept 14 days.", ["# Runbook\n\n## Backups\nKept 14 days."]) == ["Runbook › Backups"]

    def test_a_chunk_spanning_two_sections_is_named_by_their_parent(self):
        chunk = "Error E1042 means the secret could not be read.\n\n### Fixes\nRestart the service after the rotation.\n\n## Backups\nBackups are kept for 14 days."
        assert sections(RUNBOOK, [chunk]) == ["Runbook"]

    def test_a_chunk_inside_one_subsection_keeps_its_whole_path(self):
        chunk = "Error E1042 means the secret could not be read.\n\n### Fixes\nRestart the service after the rotation."
        assert sections(RUNBOOK, [chunk]) == ["Runbook › Errors"]

    def test_headings_that_end_a_chunk_are_not_its_text(self):
        assert sections(RUNBOOK, ["Restart the service after the rotation.\n\n## Backups"]) == ["Runbook › Errors › Fixes"]

    def test_two_headings_with_the_same_title_are_different_sections(self):
        text = "# A\n## Notes\nFirst.\n# B\n## Notes\nSecond."
        assert sections(text, ["First.\n# B\n## Notes\nSecond."]) == [None]

    def test_a_chunk_before_the_first_heading_has_no_section(self):
        assert sections("Preface.\n\n# Title\nBody.", ["Preface."]) == [None]

    def test_a_document_without_headings_has_no_sections(self):
        assert sections("Plain text. Nothing else.", ["Plain text.", "Nothing else."]) == [None, None]

    def test_lines_inside_fenced_code_are_not_headings(self):
        text = "# Guide\n\n```\n# not a heading\n```\n\nAfter the code."
        assert sections(text, ["After the code."]) == ["Guide"]

    def test_closing_hashes_are_not_part_of_the_title(self):
        assert sections("## Errors ##\nBody text.", ["Body text."]) == ["Errors"]

    def test_a_chunk_with_no_place_in_the_text_has_no_section(self):
        assert sections(RUNBOOK, ["Text the document never contains."]) == [None]


class TestRagMetadataExtractorKeywords:
    def test_its_type_is_keywords(self):
        assert RagMetadataExtractorKeywords(FakeEmbeddings()).metadata_type is RagMetadataType.KEYWORDS

    def test_codes_with_digits_are_kept_and_bare_numbers_and_short_words_dropped(self):
        text = "Error E1042 is in 14 of an old log."
        found = keywords(text, [text], max_keywords = 15)[0]
        assert "E1042" in found and not {"14", "is", "in", "of", "an"} & set(found)

    def test_a_keyword_is_written_as_the_document_first_writes_it(self):
        text = "Call GetSecretValue first. Then call getsecretvalue again."
        assert keywords(text, [text], max_keywords = 15)[0].count("GetSecretValue") == 1

    def test_the_candidate_closest_to_the_chunk_comes_first(self):
        text = "Backups, backups and backups again. Zebra."
        assert keywords(text, [text], max_keywords = 1) == [["Backups"]]

    def test_at_most_max_keywords_are_kept(self):
        text = "Alpha bravo charlie delta echo foxtrot golf hotel india juliett."
        assert len(keywords(text, [text], max_keywords = 3)[0]) == 3

    def test_candidates_are_embedded_once_per_document_in_one_batch(self):
        embeddings = FakeEmbeddings()
        keywords(RUNBOOK, ["Error E1042 means the secret could not be read.", "Backups are kept for 14 days."], embeddings)
        assert len(embeddings.calls) == 1 and "E1042" in embeddings.calls[0]

    def test_a_chunk_without_words_has_no_keywords_and_costs_no_call(self):
        embeddings = FakeEmbeddings()
        assert keywords("12 34.", ["12 34."], embeddings) == [[]] and embeddings.calls == []

    def test_no_keyword_or_more_keywords_than_candidates_is_refused(self):
        for current in ({"max_keywords": 0}, {"max_keywords": 6, "candidates": 5}):
            with pytest.raises(ValueError):
                RagMetadataExtractorKeywords(FakeEmbeddings(), **current)


class TestRagMetadataExtractorTopic:
    def test_its_type_is_topic(self):
        assert RagMetadataExtractorTopic(FAKE_TOPIC_INDEX).metadata_type is RagMetadataType.TOPIC

    def test_each_chunk_gets_the_topic_nearest_its_vector_and_the_similarity(self):
        chunks = ["The coffee machine is cleaned on Fridays.", "Error codes: the secret could not be read."]
        document = make_document(" ".join(chunks), chunks)
        found = RagMetadataExtractorTopic(FAKE_TOPIC_INDEX).apply(document, make_metadata(document))
        assert [current.topic for current in found] == ["Office", "Errors"]
        assert found[0].topic_score == FAKE_TOPIC_INDEX.nearest(document.vectors[0])[1]


class TestRagMetadataAttacher:
    def attach(self, text, chunks):
        return RagMetadataAttacher(FAKE_TOPIC_INDEX, FakeEmbeddings()).attach(make_document(text, chunks))

    def test_every_chunk_gets_its_source_and_span(self):
        chunks = ["Error E1042 means the secret could not be read.", "Backups are kept for 14 days."]
        found = self.attach(RUNBOOK, chunks)
        assert [(current.source.document_id, current.source.title, current.source.chunk_index) for current in found] == [
            ("d1", "guide.md", 0), ("d1", "guide.md", 1)
        ]
        assert [RUNBOOK[current.source.start:current.source.end] for current in found] == chunks

    def test_a_repeated_chunk_is_placed_after_the_one_before_it(self):
        text = "Backups are kept. Backups are kept."
        found = self.attach(text, ["Backups are kept.", "Backups are kept."])
        assert [current.source.start for current in found] == [0, 18]

    def test_overlapping_chunks_are_placed_where_each_starts(self):
        text = "one two three four five"
        found = self.attach(text, ["one two three", "three four five"])
        assert [(current.source.start, current.source.end) for current in found] == [(0, 13), (8, 23)]

    def test_a_chunk_that_is_not_in_the_text_has_no_span(self):
        found = self.attach(RUNBOOK, ["Text the document never contains."])
        assert (found[0].source.start, found[0].source.end) == (None, None)

    def test_it_fills_section_topic_and_keywords(self):
        found = self.attach(RUNBOOK, ["Error E1042 means the secret could not be read."])[0]
        assert found.section == "Runbook › Errors" and found.topic == "Errors" and "E1042" in found.keywords

    def test_the_extractors_run_in_the_order_its_types_name(self):
        attacher = RagMetadataAttacher(FAKE_TOPIC_INDEX, FakeEmbeddings())
        assert [current.metadata_type for current in attacher._extractors] == list(RagMetadataAttacher.EXTRACTOR_TYPES)
        assert set(RagMetadataAttacher.EXTRACTOR_TYPES) == set(RagMetadataType)


class TestRagMetadataExtractorsFactory:
    def test_every_type_is_registered(self):
        assert set(RAG_METADATA_EXTRACTORS_REGISTRY) == set(RagMetadataType)

    def test_it_builds_each_type_with_forwarded_arguments(self):
        factory = RagMetadataExtractorsFactory()
        keywords_extractor = factory.create(RagMetadataType.KEYWORDS, embeddings = FakeEmbeddings(), max_keywords = 2)
        assert isinstance(factory.create(RagMetadataType.SECTION), RagMetadataExtractorSection)
        assert factory.create(RagMetadataType.TOPIC, topic_index = FAKE_TOPIC_INDEX)._topic_index is FAKE_TOPIC_INDEX
        assert isinstance(keywords_extractor, RagMetadataExtractorKeywords) and keywords_extractor._max_keywords == 2

    def test_an_unknown_type_raises_value_error(self):
        with pytest.raises(ValueError):
            RagMetadataExtractorsFactory().create("unknown")
