import math
import heapq

from app.intelligence.agents import RagChunkSearchBase
from app.intelligence.agents import RagChunkSearchType


class RagChunkSearchAStar(RagChunkSearchBase):
    """A* search over states (next sentence, start of the current chunk). From each
    state the chunk is extended by the next sentence unless it would grow too long, or
    cut before it once it is long enough and enough text is left for another; a chunk
    that cannot grow must be cut. Every state is expanded once, at its cheapest cost.

    The heuristic is the fewest cuts the remaining characters still need times the
    cheapest cut. It never overestimates and is consistent, so the cut found is the
    cheapest allowed one."""

    @property
    def search_type(self) -> RagChunkSearchType:
        return RagChunkSearchType.A_STAR

    def search(self, lengths: list[int], cut_costs: list[float],
        extend_costs: dict[tuple[int, int], float]) -> list[int]:
        count = len(lengths)
        if count == 0:
            return []

        remaining = [0] * (count + 1)
        for index in range(count - 1, -1, -1):
            remaining[index] = remaining[index + 1] + lengths[index]
        cheapest_cut = min(cut_costs[1:], default = 0.0)

        def heuristic(index: int, chars: int) -> float:
            overflow = remaining[index] - (self._chunk_chars - chars)
            return max(0, math.ceil(overflow / self._chunk_chars)) * cheapest_cut

        best: dict[tuple[int, int], float] = {(1, 0): 0.0}
        parents: dict[tuple[int, int], tuple[int, int] | None] = {}
        frontier = [(heuristic(1, lengths[0]), 0.0, 1, 0, None)]

        while frontier:
            _, cost, index, start, parent = heapq.heappop(frontier)
            if (index, start) in parents:
                continue
            parents[(index, start)] = parent
            if index == count:
                break

            chars = remaining[start] - remaining[index]
            forced = chars + lengths[index] > self._chunk_chars
            moves = []
            if not forced:
                moves.append((index + 1, start, extend_costs[(start, index)], chars + lengths[index]))
            if forced or (chars >= self._min_chars and remaining[index] >= self._min_chars):
                moves.append((index + 1, index, cut_costs[index], lengths[index]))

            for next_index, next_start, step, next_chars in moves:
                total = cost + step
                if total < best.get((next_index, next_start), math.inf):
                    best[(next_index, next_start)] = total
                    heapq.heappush(frontier, (total + heuristic(next_index, next_chars), total,
                        next_index, next_start, (index, start)))
        else:
            raise RuntimeError("No cut of the document keeps every chunk within its length limits.")

        starts: set[int] = set()
        state = (index, start)
        while state is not None:
            starts.add(state[1])
            state = parents[state]
        return sorted(starts)
