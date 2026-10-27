from pydantic import BaseModel

from app.messages.message_ai import MessageAI
from app.outputs.output_type import OutputType
from app.outputs.output_structured import OutputStructured


class Contact(BaseModel):
    name: str
    email: str


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
