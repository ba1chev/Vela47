from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputType
from app.intelligence.outputs import OutputEntry
from tests.fixtures.outputs.sentiment import Sentiment
from app.intelligence.outputs import OutputClassification


class TestOutputClassification:
    def test_type_discriminator(self):
        out = OutputClassification(raw = MessageAI(content = ""), selected = Sentiment.POSITIVE)
        assert out.type == OutputType.CLASSIFICATION

    def test_selected_stored(self):
        out = OutputClassification(raw = MessageAI(content = ""), selected = Sentiment.NEGATIVE)
        assert out.selected == Sentiment.NEGATIVE
