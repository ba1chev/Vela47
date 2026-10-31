import json
import pytest

from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputJSON
from app.intelligence.outputs import OutputParserType
from app.intelligence.outputs import OutputParserJSON


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
