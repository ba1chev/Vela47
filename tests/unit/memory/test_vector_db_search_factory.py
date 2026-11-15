import pytest

from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchFactory
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchUninformedBFS
from app.intelligence.memory import VectorDBSearchUninformedType
from app.intelligence.memory import VectorDBSearchInformedIDAStar


class TestVectorDBSearchFactory:
    def test_creates_uninformed_search(self):
        search = VectorDBSearchFactory().create(
            VectorDBSearchType.UNINFORMED, VectorDBSearchUninformedType.BREADTH_FIRST_SEARCH,
            graph = {}
        )
        assert isinstance(search, VectorDBSearchUninformedBFS)

    def test_creates_informed_search(self):
        search = VectorDBSearchFactory().create(
            VectorDBSearchType.INFORMED, VectorDBSearchInformedType.ITERATIVE_DEEPENING_A_STAR_SEARCH,
            graph = {}, heuristics = lambda node: 0
        )
        assert isinstance(search, VectorDBSearchInformedIDAStar)

    def test_algorithm_of_other_family_raises(self):
        with pytest.raises(ValueError):
            VectorDBSearchFactory().create(
                VectorDBSearchType.UNINFORMED, VectorDBSearchInformedType.A_STAR_SEARCH
            )
