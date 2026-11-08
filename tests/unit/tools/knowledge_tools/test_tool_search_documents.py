from app.intelligence.agents import RagIndexer
from app.intelligence.memory import VectorDbMemory
from app.intelligence.tools import ToolSearchDocuments
from app.intelligence.agents import RagChunkerRecursive
from app.intelligence.tools import ToolSearchDocumentsInput
from tests.fixtures.model.fake_embeddings import FakeEmbeddings

GUIDE = (
    "Error E1042 means the RDS secret could not be read.\n\n"
    "Backups run nightly at two in the morning.\n\n"
    "Deployments go through the staging cluster first."
)


def make_tool(documents = None):
    embeddings = FakeEmbeddings()
    indexer = RagIndexer(RagChunkerRecursive(chunk_chars = 60, overlap_chars = 0), embeddings)
    memory = VectorDbMemory(embeddings)
    for current_id, (current_title, current_text) in enumerate((documents or {}).items()):
        memory.add_entries(indexer.index(f"d{current_id}", current_title, current_text))
    return ToolSearchDocuments(memory)


class TestToolSearchDocuments:
    def test_name_is_stable(self):
        assert make_tool().name == "search_documents"

    def test_no_documents_is_said_plainly(self):
        assert "has not uploaded any documents" in make_tool().execute(ToolSearchDocumentsInput(query = "E1042"))

    def test_the_best_passage_comes_first_with_its_document_and_part(self):
        output = make_tool({"runbook.md": GUIDE}).execute(ToolSearchDocumentsInput(query = "error E1042 secret"))
        assert "[1] runbook.md, part 1\nError E1042 means the RDS secret" in output

    def test_top_k_bounds_the_passages(self):
        output = make_tool({"runbook.md": GUIDE}).execute(ToolSearchDocumentsInput(query = "the", top_k = 2))
        assert "[2]" in output and "[3]" not in output

    def test_passages_from_every_document_can_be_found(self):
        tool = make_tool({"runbook.md": GUIDE, "notes.md": "The staging cluster lives in eu-west-1."})
        output = tool.execute(ToolSearchDocumentsInput(query = "staging cluster eu-west-1", top_k = 1))
        assert "notes.md" in output

    def test_a_long_passage_is_cut(self):
        tool = make_tool({"long.md": "word " * 2000})
        tool.MAX_PASSAGE_CHARS = 50
        output = tool.execute(ToolSearchDocumentsInput(query = "word", top_k = 1))
        assert output.rstrip().endswith("…") and len(output) < 200
