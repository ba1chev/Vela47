from app.outputs.output_parser.output_parser_base import OutputParserBase
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_text import OutputParserText
from app.outputs.output_parser.output_parser_json import OutputParserJSON
from app.outputs.output_parser.output_parser_list import OutputParserList
from app.outputs.output_parser.output_parser_structured import OutputParserStructured
from app.outputs.output_parser.output_parser_classification import OutputParserClassification


OUTPUT_PARSER_REGISTRY: dict[OutputParserType, type[OutputParserBase]] = {
    OutputParserType.TEXT: OutputParserText,
    OutputParserType.JSON: OutputParserJSON,
    OutputParserType.STRUCTURED: OutputParserStructured,
    OutputParserType.LIST: OutputParserList,
    OutputParserType.CLASSIFICATION: OutputParserClassification
}
