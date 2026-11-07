import io
import pytest
import zipfile

from app.intelligence.loaders import LoaderDocx
from app.intelligence.loaders import LoaderType
from tests.fixtures.loaders.docx_builder import DocxBuilder


class TestLoaderDocx:
    def test_paragraphs_and_tables_keep_their_order(self):
        text = LoaderDocx().load(DocxBuilder().build()).text
        assert text.index("Run the migration") < text.index("Migrate | Ana") < text.index("Then restart")

    def test_headings_and_list_items_become_markdown(self):
        text = LoaderDocx().load(DocxBuilder().build()).text
        assert "# Deployment" in text.split("\n") and "- Check the logs." in text.split("\n")

    def test_table_rows_are_cells_joined_by_bars(self):
        assert "Step | Owner\nMigrate | Ana" in LoaderDocx().load(DocxBuilder().build()).text

    def test_the_core_title_is_read(self):
        document = LoaderDocx().load(DocxBuilder().build(title = "Runbook"))
        assert document.title == "Runbook" and document.loader_type is LoaderType.DOCX

    def test_bytes_that_are_not_a_docx_are_refused(self):
        with pytest.raises(ValueError, match = "not a Word document"):
            LoaderDocx().load(b"%PDF-1.4 nope")

    def test_an_archive_that_inflates_past_the_limit_is_refused_before_parsing(self):
        loader = LoaderDocx()
        loader.MAX_UNCOMPRESSED_BYTES = 1000
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "a" * 5000)
        with pytest.raises(ValueError, match = "expands"):
            loader.load(buffer.getvalue())

    def test_a_zip_that_is_not_a_word_document_is_refused(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("readme.txt", "hi")
        with pytest.raises(ValueError, match = "could not be opened"):
            LoaderDocx().load(buffer.getvalue())
