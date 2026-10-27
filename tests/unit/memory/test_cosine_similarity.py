import pytest

from app.memory.vector_db_memory.vector_db_operation.vector_db_utils import cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_symmetry(self):
        a, b = [0.6, 0.8], [0.8, 0.6]
        assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))
