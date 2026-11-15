import pytest

from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchApproximateHNSW
from app.intelligence.memory import VectorDBSearchApproximateType
from app.intelligence.memory import VectorDBSearchApproximateFactory


class TestVectorDBSearchApproximateFactory:
    def test_forwards_parameters(self):
        index = VectorDBSearchApproximateFactory().create(
            VectorDBSearchApproximateType.HIERARCHICAL_NAVIGABLE_SMALL_WORLD,
            top_k = 1, vectors = {"a": [1.0, 0.0], "b": [0.0, 1.0]}
        )
        assert isinstance(index, VectorDBSearchApproximateHNSW)
        assert index.search(None, [0.0, 1.0]) == ["b"]

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            VectorDBSearchApproximateFactory().create(VectorDBSearchInformedType.A_STAR_SEARCH)
