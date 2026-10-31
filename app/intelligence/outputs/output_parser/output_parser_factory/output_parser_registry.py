from app.intelligence.outputs import OutputParserBase
from app.intelligence.outputs import OutputParserType
from app.intelligence.outputs import OutputParserText
from app.intelligence.outputs import OutputParserJSON
from app.intelligence.outputs import OutputParserList
from app.intelligence.outputs import OutputParserStructured
from app.intelligence.outputs import OutputParserClassification


OUTPUT_PARSER_REGISTRY: dict[OutputParserType, type[OutputParserBase]] = {
    OutputParserType.TEXT: OutputParserText,
    OutputParserType.JSON: OutputParserJSON,
    OutputParserType.STRUCTURED: OutputParserStructured,
    OutputParserType.LIST: OutputParserList,
    OutputParserType.CLASSIFICATION: OutputParserClassification
}
