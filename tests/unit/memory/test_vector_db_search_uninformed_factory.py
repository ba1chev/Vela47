import pytest

from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchUninformedDFS
from app.intelligence.memory import VectorDBSearchUninformedDLS
from app.intelligence.memory import VectorDBSearchUninformedType
from app.intelligence.memory import VectorDBSearchUninformedFactory


GRAPH = {1: {2}, 2: {3}, 3: set()}


class TestVectorDBSearchUninformedFactory:
    def test_creates_registered_type(self):
        search = VectorDBSearchUninformedFactory().create(
            VectorDBSearchUninformedType.DEPTH_FIRST_SEARCH, graph = GRAPH
        )
        assert isinstance(search, VectorDBSearchUninformedDFS)

    def test_forwards_parameters(self):
        search = VectorDBSearchUninformedFactory().create(
            VectorDBSearchUninformedType.DEPTH_LIMITED_SEARCH, graph = GRAPH, tolerance = 1
        )
        assert isinstance(search, VectorDBSearchUninformedDLS)
        assert search.search(1, 3) is False

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            VectorDBSearchUninformedFactory().create(VectorDBSearchInformedType.A_STAR_SEARCH)
