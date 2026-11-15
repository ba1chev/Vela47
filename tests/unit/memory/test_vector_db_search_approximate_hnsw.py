import pytest
from random import Random

from app.intelligence.memory import cosine_similarity
from app.intelligence.memory import VectorDBSearchType
from app.intelligence.memory import VectorDBSearchApproximateHNSW
from app.intelligence.memory import VectorDBSearchApproximateType


def clustered_vectors(count, dimensions, clusters, seed):
    random = Random(seed)
    centers = [[random.gauss(0, 1) for _ in range(dimensions)] for _ in range(clusters)]
    return {
        node: [value + random.gauss(0, 0.3) for value in centers[node % clusters]]
        for node in range(count)
    }


def exact_nearest(vectors, query, top_k):
    return sorted(vectors, key = lambda node: -cosine_similarity(query, vectors[node]))[:top_k]


VECTORS = clustered_vectors(300, 16, 10, seed = 1)


class TestVectorDBSearchApproximateHNSW:
    def test_types(self):
        index = VectorDBSearchApproximateHNSW(top_k = 3)
        assert index.search_type == VectorDBSearchType.APPROXIMATE
        assert index.approximate_type == VectorDBSearchApproximateType.HIERARCHICAL_NAVIGABLE_SMALL_WORLD

    def test_empty_index_returns_nothing(self):
        assert VectorDBSearchApproximateHNSW(top_k = 3).search(None, [1.0, 0.0]) == []

    def test_finds_exact_neighbours_on_small_index(self):
        vectors = {"x": [1.0, 0.0], "y": [0.0, 1.0], "xy": [1.0, 1.0], "-x": [-1.0, 0.0]}
        index = VectorDBSearchApproximateHNSW(top_k = 2, vectors = vectors, seed = 0)
        assert index.search(None, [0.9, 0.1]) == ["x", "xy"]

    def test_recall_against_brute_force(self):
        index = VectorDBSearchApproximateHNSW(top_k = 10, vectors = VECTORS, seed = 7)
        queries = clustered_vectors(20, 16, 10, seed = 1)
        hits = sum(
            len(set(index.search(None, query)) & set(exact_nearest(VECTORS, query, 10)))
            for query in queries.values()
        )
        assert hits / 200 >= 0.95

    def test_results_are_closest_first_and_capped(self):
        index = VectorDBSearchApproximateHNSW(top_k = 5, vectors = VECTORS, seed = 7)
        result = index.search(None, VECTORS[42])
        distances = [1.0 - cosine_similarity(VECTORS[42], VECTORS[node]) for node in result]
        assert len(result) == 5
        assert result[0] == 42
        assert distances == sorted(distances)

    def test_vectors_added_later_are_found(self):
        index = VectorDBSearchApproximateHNSW(top_k = 1, vectors = VECTORS, seed = 7)
        index.add("new", [5.0] * 16)
        assert index.search(None, [5.0] * 16) == ["new"]

    def test_search_from_given_start(self):
        index = VectorDBSearchApproximateHNSW(top_k = 1, vectors = VECTORS, seed = 7)
        assert index.search(0, VECTORS[42]) == [42]

    def test_duplicate_node_raises(self):
        index = VectorDBSearchApproximateHNSW(top_k = 1, vectors = {"a": [1.0]})
        with pytest.raises(ValueError):
            index.add("a", [2.0])

    def test_unknown_start_raises(self):
        index = VectorDBSearchApproximateHNSW(top_k = 1, vectors = {"a": [1.0]})
        with pytest.raises(ValueError):
            index.search("b", [1.0])
