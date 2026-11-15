from math import log
from random import Random
from itertools import count
from heapq import heappop, heappush
from collections.abc import Hashable

from app.intelligence.memory import cosine_similarity
from app.intelligence.memory import VectorDBSearchApproximateBase
from app.intelligence.memory import VectorDBSearchApproximateType


class VectorDBSearchApproximateHNSW(VectorDBSearchApproximateBase):
    """Hierarchical navigable small world index over cosine distance (Malkov and
    Yashunin). Every vector gets a random top layer; each layer is a proximity graph
    in the shape the uninformed searches walk, sparser the higher it is. A search
    descends greedily from the top entry point to layer 0, then runs a beam search of
    width ef_search there. A neighbour is linked only if it is closer to the new node
    than to the neighbours already linked, which keeps edges between clusters. m,
    ef_construction and ef_search default to pgvector's 16, 64 and 40; a larger
    ef_search finds more of the true neighbours, more slowly."""

    def __init__(self, top_k: int, vectors: dict[Hashable, list[float]] | None = None,
        m: int = 16, ef_construction: int = 64, ef_search: int = 40,
        seed: int | None = None) -> None:
        self._top_k = top_k
        self._m = m
        self._ef_construction = ef_construction
        self._ef_search = ef_search
        self._level_multiplier = 1 / log(m)
        self._random = Random(seed)
        self._vectors: dict[Hashable, list[float]] = {}
        self._layers: list[dict[Hashable, set[Hashable]]] = []
        self._entry_point: Hashable | None = None

        for node, vector in (vectors or {}).items():
            self.add(node, vector)

    @property
    def approximate_type(self) -> VectorDBSearchApproximateType:
        return VectorDBSearchApproximateType.HIERARCHICAL_NAVIGABLE_SMALL_WORLD

    def add(self, node: Hashable, vector: list[float]) -> None:
        if node in self._vectors:
            raise ValueError(f"Node '{node}' is already in the index.")

        level = int(-log(1.0 - self._random.random()) * self._level_multiplier)
        top_level = len(self._layers) - 1
        self._vectors[node] = vector
        while len(self._layers) <= level:
            self._layers.append({})
        for layer in range(level + 1):
            self._layers[layer][node] = set()

        if self._entry_point is None:
            self._entry_point = node
            return

        entry_points = [self._entry_point]
        for layer in range(top_level, level, -1):
            entry_points = self._search_layer(vector, entry_points, 1, layer)

        for layer in range(min(top_level, level), -1, -1):
            candidates = self._search_layer(vector, entry_points, self._ef_construction, layer)
            for neighbour in self._select_neighbours(vector, candidates, self._m):
                self._layers[layer][node].add(neighbour)
                self._layers[layer][neighbour].add(node)
                self._shrink(neighbour, layer)
            entry_points = candidates

        if level > top_level:
            self._entry_point = node

    def search(self, start_state: Hashable | None, goal_state: list[float]) -> list[Hashable]:
        if self._entry_point is None:
            return []

        if start_state is not None:
            if start_state not in self._vectors:
                raise ValueError(f"Node '{start_state}' is not in the index.")
            entry_points = [start_state]
        else:
            entry_points = [self._entry_point]
            for layer in range(len(self._layers) - 1, 0, -1):
                entry_points = self._search_layer(goal_state, entry_points, 1, layer)

        ef = max(self._ef_search, self._top_k)
        return self._search_layer(goal_state, entry_points, ef, 0)[:self._top_k]

    def _search_layer(self, query: list[float], entry_points: list[Hashable],
        ef: int, layer: int) -> list[Hashable]:
        sequence = count()
        visited: set[Hashable] = set(entry_points)
        candidates: list[tuple[float, int, Hashable]] = []
        results: list[tuple[float, int, Hashable]] = []

        for entry_point in entry_points:
            entry_distance = self._distance(query, entry_point)
            heappush(candidates, (entry_distance, next(sequence), entry_point))
            heappush(results, (-entry_distance, next(sequence), entry_point))
            if len(results) > ef:
                heappop(results)

        while candidates:
            current_distance, _, current_node = heappop(candidates)
            if current_distance > -results[0][0]:
                break

            for current_neighbour in self._layers[layer].get(current_node, set()):
                if current_neighbour in visited:
                    continue
                visited.add(current_neighbour)

                neighbour_distance = self._distance(query, current_neighbour)
                if len(results) < ef or neighbour_distance < -results[0][0]:
                    heappush(candidates, (neighbour_distance, next(sequence), current_neighbour))
                    heappush(results, (-neighbour_distance, next(sequence), current_neighbour))
                    if len(results) > ef:
                        heappop(results)

        return [node for _, _, node in sorted(results, reverse = True)]

    def _shrink(self, node: Hashable, layer: int) -> None:
        neighbours = self._layers[layer][node]
        limit = self._m * 2 if layer == 0 else self._m
        if len(neighbours) <= limit:
            return

        vector = self._vectors[node]
        closest = sorted(neighbours, key = lambda neighbour: self._distance(vector, neighbour))
        self._layers[layer][node] = set(self._select_neighbours(vector, closest, limit))

    def _select_neighbours(self, vector: list[float], candidates: list[Hashable],
        limit: int) -> list[Hashable]:
        selected: list[Hashable] = []
        for current_candidate in candidates:
            if len(selected) >= limit:
                break

            candidate_distance = self._distance(vector, current_candidate)
            if all(
                candidate_distance < self._distance(self._vectors[current_selected], current_candidate)
                for current_selected in selected
            ):
                selected.append(current_candidate)

        return selected

    def _distance(self, query: list[float], node: Hashable) -> float:
        return 1.0 - cosine_similarity(query, self._vectors[node])
