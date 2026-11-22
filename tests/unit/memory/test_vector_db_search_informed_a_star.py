from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchEdge
from app.intelligence.memory import VectorDBSearchInformedType
from app.intelligence.memory import VectorDBSearchInformedAStar


def edge(to, weight):
    return VectorDBSearchEdge(to = to, weight = weight)


GRAPH = {
    "S": [edge("A", 1), edge("B", 4)],
    "A": [edge("B", 2), edge("C", 5)],
    "B": [edge("C", 1)],
    "C": []
}
HEURISTICS = {"S": 3, "A": 2, "B": 1, "C": 0}
DETOUR_GRAPH = {
    "S": [edge("A", 1), edge("B", 1)],
    "A": [edge("C", 1)],
    "B": [edge("C", 3)],
    "C": [edge("G", 3)],
    "G": []
}
DETOUR_HEURISTICS = {"S": 0, "A": 4, "B": 0, "C": 0, "G": 0}


class TestVectorDBSearchInformedAStar:
    def test_types(self):
        search = VectorDBSearchInformedAStar(GRAPH, HEURISTICS.get)
        assert search.search_type == VectorDBSearchType.INFORMED
        assert search.informed_type == VectorDBSearchInformedType.A_STAR_SEARCH

    def test_returns_cheapest_path(self):
        result = VectorDBSearchInformedAStar(GRAPH, HEURISTICS.get).search("S", "C")
        assert result == ["S", "A", "B", "C"]

    def test_an_admissible_but_inconsistent_heuristic_still_finds_the_cheapest_path(self):
        result = VectorDBSearchInformedAStar(DETOUR_GRAPH, DETOUR_HEURISTICS.get).search("S", "G")
        assert result == ["S", "A", "C", "G"]

    def test_unreachable_goal(self):
        assert VectorDBSearchInformedAStar(GRAPH, HEURISTICS.get).search("C", "S") == []

    def test_start_is_goal(self):
        assert VectorDBSearchInformedAStar(GRAPH, HEURISTICS.get).search("S", "S") == ["S"]
