import json
import pytest
from pydantic import BaseModel, ValidationError

from app.intelligence.messages import MessageAI
from tests.fixtures.outputs.contact import Contact
from app.intelligence.outputs import OutputStructured
from app.intelligence.outputs import OutputParserType
from app.intelligence.outputs import OutputParserStructured


class TestOutputParserStructured:
    def setup_method(self):
        self.parser = OutputParserStructured(schema = Contact)

    def test_parser_type(self):
        assert self.parser.parser_type == OutputParserType.STRUCTURED

    def test_validates_schema(self):
        data = json.dumps({"name": "Yoan", "email": "y@test.com"})
        result = self.parser.parse(MessageAI(content = data))
        assert isinstance(result, OutputStructured)
        assert isinstance(result.data, Contact)
        assert result.data.name == "Yoan"

    def test_invalid_schema_raises(self):
        with pytest.raises(ValidationError):
            self.parser.parse(MessageAI(content = json.dumps({"wrong_field": "x"})))

    def test_json_in_a_markdown_code_block_is_unwrapped(self):
        data = json.dumps({"name": "Yoan", "email": "y@test.com"})
        for content in (f"```json\n{data}\n```", f"```\n{data}\n```", f"  ```json\n{data}```  "):
            assert self.parser.parse(MessageAI(content = content)).data.name == "Yoan"

    def test_text_around_a_code_block_is_still_refused(self):
        data = json.dumps({"name": "Yoan", "email": "y@test.com"})
        with pytest.raises(ValidationError):
            self.parser.parse(MessageAI(content = f"Here is the plan:\n```json\n{data}\n```"))
