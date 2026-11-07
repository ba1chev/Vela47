from app.intelligence.loaders import LoaderText
from app.intelligence.loaders import LoaderType


class TestLoaderText:
    def test_utf8_text_is_returned_as_is(self):
        document = LoaderText().load("Грешка E1042 — secret.".encode("utf-8"))
        assert document.text == "Грешка E1042 — secret." and document.loader_type is LoaderType.TEXT

    def test_a_byte_order_mark_is_dropped(self):
        assert LoaderText().load(b"\xef\xbb\xbfhello").text == "hello"

    def test_the_declared_encoding_is_used(self):
        assert LoaderText().load("café".encode("latin-1"), "latin-1").text == "café"

    def test_a_wrong_declared_encoding_falls_back_to_utf8(self):
        assert LoaderText().load("ok".encode("utf-8"), "no-such-codec").text == "ok"

    def test_legacy_bytes_are_read_rather_than_refused(self):
        assert LoaderText().load(b"caf\xe9").text == "café"

    def test_blank_lines_are_collapsed_to_one(self):
        assert LoaderText().load(b"one  \n\n\n\ntwo\r\n").text == "one\n\ntwo"

    def test_a_text_file_has_no_title(self):
        assert LoaderText().load(b"x").title is None
