from app.messages.message_ai import MessageAI
from app.outputs.output_type import OutputType
from app.outputs.output_list import OutputList


class TestOutputList:
    def test_type_discriminator(self):
        out = OutputList(raw = MessageAI(content = ""), items = [])
        assert out.type == OutputType.LIST

    def test_items_stored(self):
        out = OutputList(raw = MessageAI(content = ""), items = ["a", "b", "c"])
        assert out.items == ["a", "b", "c"]
