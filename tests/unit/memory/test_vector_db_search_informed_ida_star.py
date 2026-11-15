from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedIDAStar


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 4)],
    "A": [edge("B", 2), edge("C", 5)],
    "B": [edge("C", 1)],
    "C": []
}
HEURISTICS = {"S": 3, "A": 2, "B": 1, "C": 0}


def heuristics(node):
    return HEURISTICS.get(node, 0)


class TestVectorDBSearchInformedIDAStar:
    def test_type(self):
        search = VectorDBSearchInformedIDAStar(GRAPH, heuristics)
        assert search.informed_type == VectorDBSearchInformedType.ITERATIVE_DEEPENING_A_STAR_SEARCH

    def test_returns_cheapest_cost(self):
        assert VectorDBSearchInformedIDAStar(GRAPH, heuristics).search("S", "C") == 4

    def test_unreachable_goal(self):
        assert VectorDBSearchInformedIDAStar(GRAPH, heuristics).search("S", "Z") == -1

    def test_start_is_goal(self):
        assert VectorDBSearchInformedIDAStar(GRAPH, heuristics).search("C", "C") == 0
