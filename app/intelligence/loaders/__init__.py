# Turns uploaded files and fetched pages into the plain text agents read and index.

from app.intelligence.loaders.loader_type import LoaderType
from app.intelligence.loaders.loader_document import LoaderDocument
from app.intelligence.loaders.loader_base import LoaderBase
from app.intelligence.loaders.loader_text import LoaderText
from app.intelligence.loaders.loader_html_parser import LoaderHtmlParser
from app.intelligence.loaders.loader_html import LoaderHtml
from app.intelligence.loaders.loader_pdf import LoaderPdf
from app.intelligence.loaders.loader_docx import LoaderDocx
from app.intelligence.loaders.loader_type_resolver import LOADER_TYPE_CONTENT_TYPES, LOADER_TYPE_EXTENSIONS, resolve_loader_type
from app.intelligence.loaders.loaders_factory.loaders_registry import LOADERS_REGISTRY
from app.intelligence.loaders.loaders_factory.loaders_factory_base import LoadersFactoryBase
from app.intelligence.loaders.loaders_factory.loaders_factory import LoadersFactory

__all__ = [
    "LoaderType",
    "LoaderDocument",
    "LoaderBase",
    "LoaderText",
    "LoaderHtmlParser",
    "LoaderHtml",
    "LoaderPdf",
    "LoaderDocx",
    "LOADER_TYPE_CONTENT_TYPES",
    "LOADER_TYPE_EXTENSIONS",
    "resolve_loader_type",
    "LOADERS_REGISTRY",
    "LoadersFactoryBase",
    "LoadersFactory"
]
