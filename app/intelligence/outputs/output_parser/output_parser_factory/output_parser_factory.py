from typing import Any

from app.intelligence.outputs.output_parser.output_parser_base import OutputParserBase
from app.intelligence.outputs.output_parser.output_parser_type import OutputParserType
from app.intelligence.outputs.output_parser.output_parser_factory.output_parser_registry import OUTPUT_PARSER_REGISTRY
from app.intelligence.outputs.output_parser.output_parser_factory.output_parser_base_factory import OutputParserBaseFactory


class OutputParserFactory(OutputParserBaseFactory):
    """Concrete factory that maps each OutputParserType to its corresponding
    OutputParserBase subclass and delegates construction to it. Additional
    keyword arguments are forwarded verbatim, so callers can supply
    parser-specific parameters — such as a Pydantic schema for STRUCTURED or
    a delimiter for LIST — without the factory needing to know about them
    explicitly.

    Registry reference:
      TEXT           -> OutputParserText()
      JSON           -> OutputParserJSON()
      STRUCTURED     -> OutputParserStructured(schema=<BaseModel subclass>)
      LIST           -> OutputParserList(delimiter=<str>, default "\\n")
      CLASSIFICATION -> OutputParserClassification(entry_type=<OutputEntry subclass>)"""

    def create(self, type: OutputParserType, **kwargs: Any) -> OutputParserBase:
        cls = OUTPUT_PARSER_REGISTRY.get(type)

        if cls is None:
            raise ValueError(
                f"No parser class registered for type '{type}'. "
                f"Known types: {list(OUTPUT_PARSER_REGISTRY)}"
            )

        return cls(**kwargs)
