from app.messages.message_ai import MessageAI
from app.outputs.output_type import OutputType
from app.outputs.output_text import OutputText


class TestOutputText:
    def test_type_discriminator(self):
        msg = MessageAI(content = "hello")
        out = OutputText(raw = msg, text = "hello")
        assert out.type == OutputType.TEXT

    def test_text_stored(self):
        msg = MessageAI(content = "hello world")
        out = OutputText(raw = msg, text = "hello world")
        assert out.text == "hello world"

    def test_raw_preserved(self):
        msg = MessageAI(content = "x")
        out = OutputText(raw = msg, text = "x")
        assert out.raw is msg
