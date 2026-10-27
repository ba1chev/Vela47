import json
import pytest
from pydantic import BaseModel, ValidationError

from app.messages.message_ai import MessageAI
from app.outputs.output_structured import OutputStructured
from app.outputs.output_parser.output_parser_type import OutputParserType
from app.outputs.output_parser.output_parser_structured import OutputParserStructured


class Contact(BaseModel):
    name: str
    email: str


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
