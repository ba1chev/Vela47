import json
import pytest

from app.messages.message_ai import MessageAI
from app.outputs.output_json import OutputJSON
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_json import OutputParserJSON


class TestOutputParserJSON:
    def setup_method(self):
        self.parser = OutputParserJSON()

    def test_parser_type(self):
        assert self.parser.parser_type == OutputParserType.JSON

    def test_parses_object(self):
        result = self.parser.parse(MessageAI(content = json.dumps({"a": 1})))
        assert isinstance(result, OutputJSON)
        assert result.data == {"a": 1}

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            self.parser.parse(MessageAI(content = "not json"))

    def test_nested_structure(self):
        data = {"outer": {"inner": [1, 2, 3]}}
        result = self.parser.parse(MessageAI(content = json.dumps(data)))
        assert result.data["outer"]["inner"] == [1, 2, 3]
