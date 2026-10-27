from app.messages.message_ai import MessageAI
from app.outputs.output_type import OutputType
from app.outputs.output_entry import OutputEntry
from app.outputs.output_classification import OutputClassification


class Sentiment(OutputEntry):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TestOutputClassification:
    def test_type_discriminator(self):
        out = OutputClassification(raw = MessageAI(content = ""), selected = Sentiment.POSITIVE)
        assert out.type == OutputType.CLASSIFICATION

    def test_selected_stored(self):
        out = OutputClassification(raw = MessageAI(content = ""), selected = Sentiment.NEGATIVE)
        assert out.selected == Sentiment.NEGATIVE
