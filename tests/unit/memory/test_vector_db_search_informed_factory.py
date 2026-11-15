import pytest

from app.intelligence.memory import VectorDBSearchInformedBeam
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchUninformedType
from app.intelligence.memory import VectorDBSearchInformedFactory


class TestVectorDBSearchInformedFactory:
    def test_forwards_parameters(self):
        search = VectorDBSearchInformedFactory().create(
            VectorDBSearchInformedType.BEAM_SEARCH,
            graph = {}, queue_limit = 2, heuristics = lambda node: 0
        )
        assert isinstance(search, VectorDBSearchInformedBeam)
        assert search.search("S", "S") == ["S"]

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            VectorDBSearchInformedFactory().create(VectorDBSearchUninformedType.DEPTH_FIRST_SEARCH)
