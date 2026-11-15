from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedHillClimbing


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 1)],
    "A": [],
    "B": [edge("G", 1)],
    "G": []
}
HEURISTICS = {"S": 2, "A": 0, "B": 1, "G": 0}


class TestVectorDBSearchInformedHillClimbing:
    def test_type(self):
        search = VectorDBSearchInformedHillClimbing(GRAPH, HEURISTICS.get)
        assert search.informed_type == VectorDBSearchInformedType.HILL_CLIMBING

    def test_climbs_to_goal(self):
        search = VectorDBSearchInformedHillClimbing(GRAPH, HEURISTICS.get)
        assert search.search("B", "G") == ["B", "G"]

    def test_stuck_at_local_optimum(self):
        search = VectorDBSearchInformedHillClimbing(GRAPH, HEURISTICS.get)
        assert search.search("S", "G") == []
