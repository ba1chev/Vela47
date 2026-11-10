from typing import Any

from app.intelligence.outputs import OutputParserBase
from app.intelligence.outputs import OutputParserType
from app.intelligence.outputs import OUTPUT_PARSER_REGISTRY
from app.intelligence.outputs import OutputParserBaseFactory


class OutputParserFactory(OutputParserBaseFactory):
    """Concrete factory that maps each OutputParserType to its OutputParserBase subclass
    through OUTPUT_PARSER_REGISTRY and delegates construction to it. Additional keyword
    arguments are forwarded verbatim, so callers can supply parser-specific parameters,
    such as a Pydantic schema for STRUCTURED or a delimiter for LIST, without the
    factory knowing about them."""

    def create(self, type: OutputParserType, **kwargs: Any) -> OutputParserBase:
        cls = OUTPUT_PARSER_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No parser class registered for type '{type}'. "
                f"Known types: {list(OUTPUT_PARSER_REGISTRY)}"
            )

        return cls(**kwargs)
