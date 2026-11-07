from app.intelligence.loaders import LoaderHtml
from app.intelligence.loaders import LoaderType


def load(markup, encoding = None):
    return LoaderHtml().load(markup.encode("utf-8") if isinstance(markup, str) else markup, encoding)


class TestLoaderHtml:
    def test_the_title_is_read_and_kept_out_of_the_text(self):
        document = load("<html><head><title> Release   notes </title></head><body><p>Body.</p></body></html>")
        assert document.title == "Release notes" and document.text == "Body." and document.loader_type is LoaderType.HTML

    def test_scripts_styles_and_navigation_are_dropped(self):
        document = load(
            "<nav><a>Home</a></nav><style>p{}</style><p>Keep me.</p>"
            "<script>var s = '<p>not text</p>';</script><footer>(c) 2026</footer>"
        )
        assert document.text == "Keep me."

    def test_a_skipped_element_is_skipped_whole_despite_nested_tags_of_its_name(self):
        document = load('<div role="navigation"><div>a</div><div>b</div></div><p>After.</p>')
        assert document.text == "After."

    def test_hidden_elements_are_dropped(self):
        assert load('<p hidden>secret</p><div aria-hidden="true">icon</div><p>Shown.</p>').text == "Shown."

    def test_structure_survives_as_markdown_like_lines(self):
        document = load("<h2>Setup</h2><p>Install it.</p><ul><li>one</li><li>two</li></ul>")
        assert document.text == "## Setup\n\nInstall it.\n\n- one\n- two"

    def test_table_rows_stay_on_their_own_lines(self):
        document = load("<table><tr><th>Key</th><th>Value</th></tr><tr><td>a</td><td>1</td></tr></table>")
        assert document.text == "Key | Value\na | 1"

    def test_whitespace_collapses_except_inside_pre(self):
        document = load("<p>a\n   b</p><pre>def f():\n    return 1</pre>")
        assert document.text == "a b\n\ndef f():\n    return 1"

    def test_entities_are_decoded(self):
        assert load("<p>Fish &amp; chips &lt;3</p>").text == "Fish & chips <3"

    def test_the_main_content_wins_when_the_page_marks_it(self):
        document = load(
            "<div>Sign in · Pricing · Blog · Careers · Contact us today for a demo</div>"
            "<main><h1>Guide</h1><p>The real content of the page, long enough to matter.</p></main>"
        )
        assert document.text == "# Guide\n\nThe real content of the page, long enough to matter."

    def test_a_tiny_marked_part_does_not_replace_the_page(self):
        document = load("<p>" + "Plenty of page text. " * 20 + "</p><article>Share</article>")
        assert document.text.startswith("Plenty of page text.") and "Share" in document.text

    def test_the_charset_is_found_in_a_meta_tag(self):
        markup = '<meta charset="windows-1251"><p>Привет</p>'.encode("windows-1251")
        assert load(markup).text == "Привет"

    def test_a_declared_encoding_takes_precedence(self):
        assert load("<p>café</p>".encode("latin-1"), "latin-1").text == "café"

    def test_a_page_without_a_title_has_none(self):
        assert load("<p>x</p>").title is None
