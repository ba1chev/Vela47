from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedBeam
from app.intelligence.memory import VectorDBSearchInformedType


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 1)],
    "A": [],
    "B": [edge("G", 1)],
    "G": []
}
HEURISTICS = {"S": 2, "A": 0, "B": 1, "G": 0}


class TestVectorDBSearchInformedBeam:
    def test_type(self):
        search = VectorDBSearchInformedBeam(GRAPH, 2, HEURISTICS.get)
        assert search.informed_type == VectorDBSearchInformedType.BEAM_SEARCH

    def test_wide_beam_finds_goal(self):
        result = VectorDBSearchInformedBeam(GRAPH, 2, HEURISTICS.get).search("S", "G")
        assert result == ["S", "B", "G"]

    def test_narrow_beam_drops_the_way_to_goal(self):
        assert VectorDBSearchInformedBeam(GRAPH, 1, HEURISTICS.get).search("S", "G") == []

    def test_start_is_goal(self):
        assert VectorDBSearchInformedBeam(GRAPH, 1, HEURISTICS.get).search("S", "S") == ["S"]
