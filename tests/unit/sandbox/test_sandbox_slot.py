import pytest
from pydantic import ValidationError

from app.intelligence.sandbox import SandboxSlot


class TestSandboxSlot:
    def test_reference_defaults_to_empty(self):
        assert SandboxSlot(id = 0).reference == ""

    def test_reference_is_preserved(self):
        assert SandboxSlot(id = 1, reference = "abc123").reference == "abc123"

    def test_negative_id_is_rejected(self):
        with pytest.raises(ValidationError):
            SandboxSlot(id = -1)
