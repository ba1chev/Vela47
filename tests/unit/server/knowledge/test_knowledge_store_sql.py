import pathlib
import tempfile

from db import DatabaseSqlite
from app.intelligence.agents import RagIndexer
from app.server.knowledge import KnowledgeDocument
from app.server.knowledge import KnowledgeStoreSql
from app.intelligence.agents import RagChunkerRecursive
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

TEXT = "Error E1042 means the RDS secret could not be read.\n\nBackups are kept for 14 days."


def make_store(path = None):
    database = DatabaseSqlite(path)
    database.start()
    return KnowledgeStoreSql(database)


def add(store, owner_id = "o1", title = "guide.md", text = TEXT):
    document = KnowledgeDocument(owner_id = owner_id, title = title, size_bytes = len(text.encode()), chunk_count = 0)
    entries = RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), FakeEmbeddings()).index(document.id, title, text)
    document = document.model_copy(update = {"chunk_count": len(entries)})
    store.add_document(document, entries)
    return document, entries


class TestKnowledgeStoreSql:
    def test_a_document_reads_back_equal_to_what_was_stored(self):
        store = make_store()
        document, _ = add(store)
        assert store.get_document(document.id) == document

    def test_an_owner_lists_only_their_own_documents(self):
        store = make_store()
        mine, _ = add(store, "me")
        add(store, "someone-else")
        assert [current.id for current in store.list_documents("me")] == [mine.id]

    def test_entries_load_back_with_their_identity_and_vectors(self):
        store = make_store()
        document, entries = add(store)
        loaded = store.load_entries("o1")
        assert [current.message.id for current in loaded] == [current.message.id for current in entries]
        assert loaded[1].message.name == "guide.md"
        assert loaded[1].message.additional_kwargs == {"document_id": document.id, "chunk_index": 1}
        assert loaded[0].vector == entries[0].vector

    def test_entries_of_other_owners_are_never_loaded(self):
        store = make_store()
        add(store, "someone-else")
        assert store.load_entries("me") == []

    def test_used_bytes_sums_an_owners_documents(self):
        store = make_store()
        add(store, text = "a" * 100)
        add(store, text = "b" * 50)
        add(store, "someone-else", text = "c" * 999)
        assert store.used_bytes("o1") == 150 and store.used_bytes("nobody") == 0

    def test_deleting_a_document_takes_its_chunks_with_it(self):
        store = make_store()
        document, _ = add(store)
        assert store.delete_document(document.id) is True
        assert store.get_document(document.id) is None and store.load_entries("o1") == []
        assert store.delete_document(document.id) is False

    def test_documents_survive_a_restart(self):
        path = pathlib.Path(tempfile.mkdtemp()) / "vela47.sqlite3"
        document, entries = add(make_store(path))
        reopened = make_store(path)
        assert reopened.get_document(document.id) == document
        assert len(reopened.load_entries("o1")) == len(entries)
