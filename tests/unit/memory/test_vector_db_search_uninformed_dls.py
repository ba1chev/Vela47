from app.intelligence.memory import VectorDBSearchUninformedDLS
from app.intelligence.memory import VectorDBSearchUninformedType


GRAPH = {1: {2, 3}, 2: {3}, 3: {4}, 4: {5}, 5: set()}


class TestVectorDBSearchUninformedDLS:
    def test_type(self):
        search = VectorDBSearchUninformedDLS(GRAPH, 3)
        assert search.uninformed_type == VectorDBSearchUninformedType.DEPTH_LIMITED_SEARCH

    def test_goal_at_the_limit(self):
        assert VectorDBSearchUninformedDLS({1: {2}, 2: {3}}, 2).search(1, 3) is True

    def test_goal_beyond_the_limit(self):
        assert VectorDBSearchUninformedDLS(GRAPH, 2).search(1, 5) is False

    def test_start_is_goal_with_zero_limit(self):
        assert VectorDBSearchUninformedDLS(GRAPH, 0).search(1, 1) is True

    def test_node_reached_shallower_is_expanded_again(self):
        assert VectorDBSearchUninformedDLS(GRAPH, 3).search(1, 5) is True
