from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import resolve_loader_type


class TestLoaderTypeResolver:
    def test_the_media_type_decides_first(self):
        assert resolve_loader_type("page.txt", "text/html; charset=utf-8") is LoaderType.HTML

    def test_any_text_media_type_is_text(self):
        assert resolve_loader_type(None, "text/markdown") is LoaderType.TEXT

    def test_known_application_types(self):
        assert resolve_loader_type(None, "application/pdf") is LoaderType.PDF
        assert resolve_loader_type(
            None, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) is LoaderType.DOCX
        assert resolve_loader_type(None, "application/json") is LoaderType.TEXT

    def test_a_generic_media_type_falls_through_to_the_name(self):
        assert resolve_loader_type("Report.PDF", "application/octet-stream") is LoaderType.PDF

    def test_a_url_is_read_for_its_extension_without_its_query(self):
        assert resolve_loader_type("https://example.org/files/guide.docx?download=1", "") is LoaderType.DOCX

    def test_text_extensions(self):
        assert all(
            resolve_loader_type(f"notes{current}") is LoaderType.TEXT
            for current in (".md", ".csv", ".log", ".yaml", ".json")
        )

    def test_nothing_recognisable_is_none(self):
        assert resolve_loader_type("photo.png", "image/png") is None
        assert resolve_loader_type("https://example.org/", None) is None
