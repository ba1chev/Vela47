from app.intelligence.outputs.output_parser.output_parser_base import OutputParserBase
from app.intelligence.outputs.output_parser.output_parser_type import OutputParserType
from app.intelligence.outputs.output_parser.output_parser_text import OutputParserText
from app.intelligence.outputs.output_parser.output_parser_json import OutputParserJSON
from app.intelligence.outputs.output_parser.output_parser_list import OutputParserList
from app.intelligence.outputs.output_parser.output_parser_structured import OutputParserStructured
from app.intelligence.outputs.output_parser.output_parser_classification import OutputParserClassification


OUTPUT_PARSER_REGISTRY: dict[OutputParserType, type[OutputParserBase]] = {
    OutputParserType.TEXT: OutputParserText,
    OutputParserType.JSON: OutputParserJSON,
    OutputParserType.STRUCTURED: OutputParserStructured,
    OutputParserType.LIST: OutputParserList,
    OutputParserType.CLASSIFICATION: OutputParserClassification
}
