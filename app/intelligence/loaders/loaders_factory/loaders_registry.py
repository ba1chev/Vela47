from app.intelligence.loaders import LoaderPdf
from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderDocx
from app.intelligence.loaders import LoaderHtml
from app.intelligence.loaders import LoaderText
from app.intelligence.loaders import LoaderType


LOADERS_REGISTRY: dict[LoaderType, type[LoaderBase]] = {
    LoaderType.TEXT: LoaderText,
    LoaderType.HTML: LoaderHtml,
    LoaderType.PDF: LoaderPdf,
    LoaderType.DOCX: LoaderDocx
}
