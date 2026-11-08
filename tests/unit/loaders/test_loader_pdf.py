import pytest

from app.intelligence.loaders import LoaderPdf
from app.intelligence.loaders import LoaderType
from tests.fixtures.loaders.pdf_builder import PdfBuilder


class TestLoaderPdf:
    def test_the_text_of_every_page_is_read_in_order(self):
        document = LoaderPdf().load(PdfBuilder().build(["First page.", "Second page."]))
        assert document.text == "First page.\n\nSecond page." and document.loader_type is LoaderType.PDF

    def test_the_metadata_title_is_read(self):
        assert LoaderPdf().load(PdfBuilder().build(["x"], title = "Runbook")).title == "Runbook"

    def test_no_metadata_title_means_none(self):
        assert LoaderPdf().load(PdfBuilder().build(["x"])).title is None

    def test_a_word_hyphenated_across_lines_is_joined(self):
        document = LoaderPdf().load(PdfBuilder().build(["hybrid retrie-\nval works"]))
        assert "retrieval works" in document.text

    def test_a_pdf_without_a_text_layer_is_refused_with_the_reason(self):
        with pytest.raises(ValueError, match = "no text layer"):
            LoaderPdf().load(PdfBuilder().build([""]))

    def test_bytes_that_are_not_a_pdf_are_refused(self):
        with pytest.raises(ValueError, match = "not a readable PDF"):
            LoaderPdf().load(b"plain text pretending")

    def test_a_damaged_pdf_that_breaks_pypdf_itself_is_refused_as_unreadable(self):
        damaged = PdfBuilder().build(["x"]).replace(b"/Size 6 /Root 1 0 R", b"/Size /Six /Root 9 0 R")
        with pytest.raises(ValueError, match = "not a readable PDF"):
            LoaderPdf().load(damaged)
