from pydantic import BaseModel

from app.intelligence.messages import MessageAI
from app.intelligence.outputs import OutputType
from tests.fixtures.outputs.contact import Contact
from app.intelligence.outputs import OutputStructured


class TestOutputStructured:
    def test_type_discriminator(self):
        contact = Contact(name = "Yoan", email = "y@test.com")
        out = OutputStructured(raw = MessageAI(content = "{}"), data = contact)
        assert out.type == OutputType.STRUCTURED

    def test_data_is_typed(self):
        contact = Contact(name = "Yoan", email = "y@test.com")
        out = OutputStructured(raw = MessageAI(content = "{}"), data = contact)
        assert isinstance(out.data, Contact)
        assert out.data.name == "Yoan"
