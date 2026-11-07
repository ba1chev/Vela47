from typing import Any

from app.intelligence.loaders import LoaderBase
from app.intelligence.loaders import LoaderType
from app.intelligence.loaders import LOADERS_REGISTRY
from app.intelligence.loaders import LoadersFactoryBase


class LoadersFactory(LoadersFactoryBase):
    """Concrete factory that maps each LoaderType to its LoaderBase subclass and delegates
    construction to it. Loaders hold no state, so a caller may build one per file or keep
    one for the process — this factory does not decide that for it.

    Registry reference:
      TEXT -> LoaderText()
      HTML -> LoaderHtml()
      PDF  -> LoaderPdf()
      DOCX -> LoaderDocx()"""

    def create(self, type: LoaderType, **kwargs: Any) -> LoaderBase:
        cls = LOADERS_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No loader class registered for type '{type}'. "
                f"Known types: {list(LOADERS_REGISTRY)}"
            )

        return cls(**kwargs)
