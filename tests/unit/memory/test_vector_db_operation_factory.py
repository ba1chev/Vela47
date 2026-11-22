import pytest

from app.intelligence.memory import VectorDbOperationType
from app.intelligence.memory import VectorDbOperationSearch
from app.intelligence.memory import VectorDbOperationFactory
from app.intelligence.memory import ContextWindowOperationType
from app.intelligence.memory import VECTOR_DB_OPERATION_REGISTRY


class TestVectorDbOperationFactory:
    def test_every_type_is_registered(self):
        assert set(VECTOR_DB_OPERATION_REGISTRY) == set(VectorDbOperationType)

    def test_creates_registered_type_with_forwarded_parameters(self):
        operation = VectorDbOperationFactory().create(VectorDbOperationType.SEARCH, query_vector = [1.0], top_k = 2)
        assert isinstance(operation, VectorDbOperationSearch)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            VectorDbOperationFactory().create(ContextWindowOperationType.SLIDE)
