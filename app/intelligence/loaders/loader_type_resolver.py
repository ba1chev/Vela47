import posixpath
from typing import Optional

from app.intelligence.loaders import LoaderType

LOADER_TYPE_CONTENT_TYPES: dict[str, LoaderType] = {
    "text/html": LoaderType.HTML,
    "application/xhtml+xml": LoaderType.HTML,
    "application/pdf": LoaderType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": LoaderType.DOCX,
    "application/json": LoaderType.TEXT,
    "application/xml": LoaderType.TEXT,
    "application/yaml": LoaderType.TEXT,
    "application/x-yaml": LoaderType.TEXT,
    "application/x-ndjson": LoaderType.TEXT
}

LOADER_TYPE_EXTENSIONS: dict[str, LoaderType] = {
    ".html": LoaderType.HTML,
    ".htm": LoaderType.HTML,
    ".xhtml": LoaderType.HTML,
    ".pdf": LoaderType.PDF,
    ".docx": LoaderType.DOCX,
    **{
        current_extension: LoaderType.TEXT
        for current_extension in (
            ".txt", ".text", ".md", ".markdown", ".rst", ".csv", ".tsv", ".json", ".jsonl",
            ".log", ".xml", ".yaml", ".yml", ".ini", ".toml"
        )
    }
}


def resolve_loader_type(file_name: Optional[str] = None,
    content_type: Optional[str] = None) -> Optional[LoaderType]:
    """Which loader can read a file, from the media type it was served or uploaded with
    and, failing that, from its name. The media type is asked first because a URL often
    has no extension at all, while a browser's upload type is often empty or the generic
    application/octet-stream — which says nothing, and so falls through to the name.
    Returns None when neither identifies a format any loader reads."""
    media_type = (content_type or "").split(";")[0].strip().lower()

    if media_type in LOADER_TYPE_CONTENT_TYPES:
        return LOADER_TYPE_CONTENT_TYPES[media_type]
    if media_type.startswith("text/"):
        return LoaderType.TEXT

    extension = posixpath.splitext((file_name or "").split("?")[0].split("#")[0].lower())[1]
    return LOADER_TYPE_EXTENSIONS.get(extension)
