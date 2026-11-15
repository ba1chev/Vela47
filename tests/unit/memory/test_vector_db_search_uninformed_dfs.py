from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchUninformedDFS
from app.intelligence.memory import VectorDBSearchUninformedType


GRAPH = {1: {2, 3}, 2: {4}, 3: {4}, 4: {5}, 5: set(), 6: {1}}


class TestVectorDBSearchUninformedDFS:
    def test_types(self):
        search = VectorDBSearchUninformedDFS(GRAPH)
        assert search.search_type == VectorDBSearchType.UNINFORMED
        assert search.uninformed_type == VectorDBSearchUninformedType.DEPTH_FIRST_SEARCH

    def test_reachable_goal(self):
        assert VectorDBSearchUninformedDFS(GRAPH).search(1, 5) is True

    def test_unreachable_goal(self):
        assert VectorDBSearchUninformedDFS(GRAPH).search(5, 1) is False

    def test_start_is_goal(self):
        assert VectorDBSearchUninformedDFS(GRAPH).search(7, 7) is True

    def test_cycle_terminates(self):
        assert VectorDBSearchUninformedDFS({1: {2}, 2: {1}}).search(1, 3) is False

    def test_searches_are_independent(self):
        search = VectorDBSearchUninformedDFS(GRAPH)
        assert search.search(1, 5) is True
        assert search.search(1, 5) is True
