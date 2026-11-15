from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchUninformedUCS
from app.intelligence.memory import VectorDBSearchUninformedType


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 4)],
    "A": [edge("B", 2), edge("C", 5)],
    "B": [edge("C", 1)],
    "C": []
}


class TestVectorDBSearchUninformedUCS:
    def test_type(self):
        search = VectorDBSearchUninformedUCS(GRAPH)
        assert search.uninformed_type == VectorDBSearchUninformedType.UNIFORM_COST_SEARCH

    def test_returns_cheapest_path(self):
        assert VectorDBSearchUninformedUCS(GRAPH).search("S", "C") == ["S", "A", "B", "C"]

    def test_unreachable_goal(self):
        assert VectorDBSearchUninformedUCS(GRAPH).search("C", "S") == []

    def test_start_is_goal(self):
        assert VectorDBSearchUninformedUCS(GRAPH).search("S", "S") == ["S"]
