from app.messages.message_ai import MessageAI
from app.outputs.output_type import OutputType
from app.outputs.output_json import OutputJSON


class TestOutputJSON:
    def test_type_discriminator(self):
        out = OutputJSON(raw = MessageAI(content = "{}"), data = {})
        assert out.type == OutputType.JSON

    def test_data_stored(self):
        data = {"key": "value", "num": 42}
        out = OutputJSON(raw = MessageAI(content = "{}"), data = data)
        assert out.data == data
