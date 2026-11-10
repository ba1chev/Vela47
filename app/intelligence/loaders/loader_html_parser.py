import re
from typing import Optional
from html.parser import HTMLParser


class LoaderHtmlParser(HTMLParser):
    """Walks an HTML page once and keeps what a reader would read (headings, paragraphs,
    list items, table rows, preformatted blocks) as Markdown-like lines. Scripts,
    styles, navigation, footers, forms and frames are dropped, counting nested tags so a
    skipped element is skipped whole.

    Text inside <main> or <article> is also collected apart and used instead of the
    whole page when it holds a real share of it. Lines inside <pre> are marked, so
    joining keeps their indentation while everywhere else whitespace collapses."""

    SKIPPED_TAGS = {
        "script", "style", "noscript", "template", "svg", "canvas", "iframe", "object",
        "embed", "nav", "footer", "aside", "form", "button", "select", "dialog"
    }
    SKIPPED_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search"}
    MAIN_TAGS = {"main", "article"}
    VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "source", "wbr"}
    PARAGRAPH_TAGS = {
        "p", "section", "article", "main", "header", "blockquote", "figure", "figcaption",
        "table", "ul", "ol", "dl", "details", "summary", "address"
    }
    LINE_TAGS = {"div", "tr", "dt", "dd", "caption"}
    ROW_TAGS = {"tr", "dt", "dd", "caption"}
    HEADING_LEVELS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
    MAIN_SHARE = 0.3
    PRESERVED = "\x00"

    def __init__(self) -> None:
        super().__init__(convert_charrefs = True)
        self._parts: list[str] = []
        self._main_parts: list[str] = []
        self._title_parts: list[str] = []
        self._skipping: Optional[list] = None
        self._main: Optional[list] = None
        self._in_title: bool = False
        self._pre_depth: int = 0
        self._cell_open: bool = False

    @property
    def title(self) -> Optional[str]:
        title = " ".join("".join(self._title_parts).split())
        return title or None

    @property
    def text(self) -> str:
        whole = self._join(self._parts)
        main = self._join(self._main_parts)
        if main and len(main) >= self.MAIN_SHARE * len(whole):
            return main
        return whole

    def _join(self, parts: list[str]) -> str:
        lines = [
            current_line.replace(self.PRESERVED, "").rstrip()
            if current_line.startswith(self.PRESERVED)
            else " ".join(current_line.split())
            for current_line in "".join(parts).split("\n")
        ]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    def _emit(self, text: str) -> None:
        self._parts.append(text)
        if self._main is not None:
            self._main_parts.append(text)

    def _is_skipped(self, tag: str, attributes: dict[str, Optional[str]]) -> bool:
        if tag in self.SKIPPED_TAGS:
            return True
        if (attributes.get("role") or "").lower() in self.SKIPPED_ROLES:
            return True
        return "hidden" in attributes or (attributes.get("aria-hidden") or "").lower() == "true"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attributes = dict(attrs)

        if self._skipping is not None:
            if tag == self._skipping[0] and tag not in self.VOID_TAGS:
                self._skipping[1] += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag not in self.VOID_TAGS and self._is_skipped(tag, attributes):
            self._skipping = [tag, 1]
            return

        if self._main is not None and tag == self._main[0]:
            self._main[1] += 1
        elif self._main is None and (tag in self.MAIN_TAGS or (attributes.get("role") or "").lower() == "main"):
            self._main = [tag, 1]

        if tag in self.HEADING_LEVELS:
            self._emit("\n\n" + "#" * self.HEADING_LEVELS[tag] + " ")
        elif tag == "li":
            self._emit("\n- ")
        elif tag == "pre":
            self._pre_depth += 1
            self._emit("\n\n" + self.PRESERVED)
        elif tag == "br":
            self._emit("\n")
        elif tag == "hr":
            self._emit("\n\n")
        elif tag in ("td", "th"):
            self._emit(" | " if self._cell_open else "")
            self._cell_open = True
        elif tag in self.PARAGRAPH_TAGS:
            self._emit("\n\n")
        elif tag in self.LINE_TAGS:
            self._cell_open = False
            self._emit("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if self._skipping is None and tag in ("br", "hr"):
            self._emit("\n" if tag == "br" else "\n\n")

    def handle_endtag(self, tag: str) -> None:
        if self._skipping is not None:
            if tag == self._skipping[0]:
                self._skipping[1] -= 1
                if self._skipping[1] == 0:
                    self._skipping = None
            return
        if tag == "title":
            self._in_title = False
            return

        if tag in self.HEADING_LEVELS or tag in self.PARAGRAPH_TAGS:
            self._emit("\n\n")
        elif tag == "pre":
            self._pre_depth = max(0, self._pre_depth - 1)
            self._emit("\n\n")
        elif tag in self.LINE_TAGS:
            self._cell_open = False
            self._emit("" if tag in self.ROW_TAGS else "\n")

        if self._main is not None and tag == self._main[0]:
            self._main[1] -= 1
            if self._main[1] == 0:
                self._main = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
            return
        if self._skipping is not None:
            return
        if self._pre_depth:
            self._emit(data.replace("\n", "\n" + self.PRESERVED))
            return
        self._emit(re.sub(r"\s+", " ", data))
