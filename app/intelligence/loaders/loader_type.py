from enum import Enum


class LoaderType(str, Enum):
    """Enumerates the kinds of file a loader can turn into plain text. Everything the RAG
    agent indexes and everything fetch_url reads passes through one of them, because
    chunking and embedding only understand text — a PDF's bytes or a page's markup would
    be indexed as noise.

    TEXT covers anything that already is text: plain text, Markdown, CSV, JSON, logs.
    HTML keeps a page's readable content and drops its navigation, scripts and styling.
    PDF reads the text layer of each page. DOCX reads a Word document's paragraphs,
    headings and tables in the order they appear."""

    TEXT = "text"
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
