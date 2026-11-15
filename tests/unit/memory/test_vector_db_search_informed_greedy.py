from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedGreedy


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 4)],
    "A": [edge("B", 2), edge("C", 5)],
    "B": [edge("C", 1)],
    "C": []
}
HEURISTICS = {"S": 3, "A": 2, "B": 1, "C": 0}


class TestVectorDBSearchInformedGreedy:
    def test_type(self):
        search = VectorDBSearchInformedGreedy(GRAPH, HEURISTICS.get)
        assert search.informed_type == VectorDBSearchInformedType.GREEDY_SEARCH

    def test_follows_heuristic_not_cost(self):
        result = VectorDBSearchInformedGreedy(GRAPH, HEURISTICS.get).search("S", "C")
        assert result == ["S", "B", "C"]

    def test_unreachable_goal(self):
        assert VectorDBSearchInformedGreedy(GRAPH, HEURISTICS.get).search("C", "S") == []

    def test_start_is_goal(self):
        assert VectorDBSearchInformedGreedy(GRAPH, HEURISTICS.get).search("S", "S") == ["S"]
