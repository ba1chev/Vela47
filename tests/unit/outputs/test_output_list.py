from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputType
from app.intelligence.outputs import OutputList


class TestOutputList:
    def test_type_discriminator(self):
        out = OutputList(raw = MessageAI(content = ""), items = [])
        assert out.type == OutputType.LIST

    def test_items_stored(self):
        out = OutputList(raw = MessageAI(content = ""), items = ["a", "b", "c"])
        assert out.items == ["a", "b", "c"]
