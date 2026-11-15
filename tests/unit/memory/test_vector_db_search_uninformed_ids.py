from app.intelligence.memory import VectorDBSearchUninformedIDS
from app.intelligence.memory import VectorDBSearchUninformedType


GRAPH = {1: {2, 3}, 2: {4}, 3: {4}, 4: {5}, 5: set()}


class TestVectorDBSearchUninformedIDS:
    def test_type(self):
        search = VectorDBSearchUninformedIDS(GRAPH, 4)
        assert search.uninformed_type == VectorDBSearchUninformedType.ITERATIVE_DEEPENING_SEARCH

    def test_goal_within_upper_bound(self):
        assert VectorDBSearchUninformedIDS(GRAPH, 4).search(1, 5) is True

    def test_upper_bound_is_exclusive(self):
        assert VectorDBSearchUninformedIDS(GRAPH, 3).search(1, 5) is False

    def test_unreachable_goal(self):
        assert VectorDBSearchUninformedIDS(GRAPH, 10).search(5, 1) is False
