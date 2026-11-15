from app.intelligence.memory import VectorDBSearchUninformedBFS
from app.intelligence.memory import VectorDBSearchUninformedType


GRAPH = {1: {2, 3}, 2: {4}, 3: {4}, 4: {5}, 5: set(), 6: {1}}


class TestVectorDBSearchUninformedBFS:
    def test_type(self):
        search = VectorDBSearchUninformedBFS(GRAPH)
        assert search.uninformed_type == VectorDBSearchUninformedType.BREADTH_FIRST_SEARCH

    def test_reachable_goal(self):
        assert VectorDBSearchUninformedBFS(GRAPH).search(6, 5) is True

    def test_unreachable_goal(self):
        assert VectorDBSearchUninformedBFS(GRAPH).search(5, 1) is False

    def test_start_is_goal(self):
        assert VectorDBSearchUninformedBFS(GRAPH).search(7, 7) is True

    def test_cycle_terminates(self):
        assert VectorDBSearchUninformedBFS({1: {2}, 2: {1}}).search(1, 3) is False
