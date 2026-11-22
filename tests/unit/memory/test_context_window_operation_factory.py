import pytest

from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import ContextWindowOperationType
from app.intelligence.memory import ContextWindowOperationSlide
from app.intelligence.memory import ContextWindowOperationFactory


class TestContextWindowOperationFactory:
    def test_creates_registered_type(self):
        operation = ContextWindowOperationFactory().create(ContextWindowOperationType.SLIDE, step = 3)
        assert isinstance(operation, ContextWindowOperationSlide)

    def test_forwards_parameters(self):
        operation = ContextWindowOperationFactory().create(ContextWindowOperationType.SHRINK, n = 1)
        assert operation.apply(["a", "b"]) == ["b"]

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            ContextWindowOperationFactory().create(VectorDbOperationType.SEARCH)
