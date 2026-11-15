from collections.abc import Hashable


def reconstruct_path(parents: dict[Hashable, Hashable], goal_node: Hashable) -> list[Hashable]:
    result: list[Hashable] = []
    current_node = goal_node
    while current_node is not None:
        result.append(current_node)
        current_node = parents.get(current_node)

    result.reverse()
    return result
