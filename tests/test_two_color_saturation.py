"""Executable differential falsification of two-color layer-saturation theorem."""
from collections import defaultdict, deque

from quixoforge.model import initial, X, O
from quixoforge import reference
from quixoforge.reachability import ReachabilityIndex


def test_two_color_monotonicity_and_layer_closure_exact_k3():
    """Independently build each (X count,O count) slice, including cycles."""
    max_stones = 3
    seeds = defaultdict(set)
    seeds[(0, 0)].add(initial())
    layers = {}
    by_k = [0] * (max_stones + 1)
    for total in range(max_stones + 1):
        for x in range(total + 1):
            o = total - x
            key = (x, o)
            visited = set(seeds[key])
            queue = deque(visited)
            while queue:
                state = queue.popleft()
                assert state.cells.count(X) == x
                assert state.cells.count(O) == o
                if reference.winner(state) is not None:
                    continue
                for move in reference.legal_moves(state):
                    child = reference.apply(state, move)
                    nxt = (child.cells.count(X), child.cells.count(O))
                    assert (nxt == key or (
                        state.turn == X and nxt == (x + 1, o) or
                        state.turn == O and nxt == (x, o + 1)
                    ))
                    if nxt == key:
                        if child not in visited:
                            visited.add(child)
                            queue.append(child)
                    elif total < max_stones:
                        seeds[nxt].add(child)
            layers[key] = visited
            by_k[total] += len(visited)
    union = set().union(*layers.values())
    independent = ReachabilityIndex.build(max_stones)
    assert len(union) == len(independent._parents) == 12297
    assert by_k == [1, 16, 468, 11812]
    assert union == set(independent._parents)
