"""Stand-alone, full RAW 5x5 reachability checker; no quixoforge imports.

This deliberately does not use D4 quotienting, packed masks, the 5x5
optimized search, or the reference module. It tests the 5-cube result
against an independently coded tuple-array transition system.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json
from time import perf_counter

EXPECTED_BY_OCCUPANCY = {0: 1, 1: 16, 2: 468, 3: 11812, 4: 187164, 5: 2055382}


def winning_mark(state):
    cells, turn = state
    lines = [cells[5*r:5*r+5] for r in range(5)]
    lines.extend(tuple(cells[5*r+c] for r in range(5)) for c in range(5))
    lines.extend((tuple(cells[6*j] for j in range(5)),
                  tuple(cells[4+4*j] for j in range(5))))
    wx = any(all(v == 1 for v in line) for line in lines)
    wo = any(all(v == -1 for v in line) for line in lines)
    return turn if wx and wo else 1 if wx else -1 if wo else None


def actions(state):
    cells, turn = state
    if winning_mark(state) is not None:
        return ()
    legal = []
    for i, mark in enumerate(cells):
        row, col = divmod(i, 5)
        if row not in (0, 4) and col not in (0, 4):
            continue
        if mark not in (0, turn):
            continue
        if col: legal.append((i, 'L'))
        if col < 4: legal.append((i, 'R'))
        if row: legal.append((i, 'U'))
        if row < 4: legal.append((i, 'D'))
    return tuple(legal)


def shift(state, move):
    cells, turn = state
    index, edge = move
    row, col = divmod(index, 5)
    step = {'L': -1, 'R': 1, 'U': -5, 'D': 5}[edge]
    count = {'L': col, 'R': 4-col, 'U': row, 'D': 4-row}[edge]
    positions = [index + j*step for j in range(count+1)]
    after = list(cells)
    for target, source in zip(positions, positions[1:]):
        after[target] = after[source]
    after[positions[-1]] = turn
    return tuple(after), -turn


def enumerate_raw(max_stones: int = 5, *, max_states: int = 2_500_000):
    if type(max_stones) is not int or not 0 <= max_stones <= 5:
        raise ValueError('verified raw domain cap must be 0..5')
    if type(max_states) is not int or max_states < 1:
        raise ValueError('max_states must be a positive integer')
    root = ((0,) * 25, 1)
    seen = {root}
    pending = deque([root])
    layers = Counter()
    candidate_actions = retained_actions = 0
    start = perf_counter()
    while pending:
        position = pending.popleft()
        cells, turn = position
        occ = 25 - cells.count(0)
        layers[occ] += 1
        for action in actions(position):
            candidate_actions += 1
            if occ == max_stones and cells[action[0]] == 0:
                continue
            child = shift(position, action)
            retained_actions += 1
            if child not in seen:
                if len(seen) >= max_states:
                    raise ValueError('raw 5x5 BFS resource cap exceeded, incomplete')
                seen.add(child)
                pending.append(child)
    result = {
        'domain': f'5x5 X-first, raw tuple-array BFS occupancy<={max_stones}',
        'reachable_states': len(seen),
        'by_occupancy': {str(i): layers[i] for i in range(max_stones + 1)},
        'candidate_actions': candidate_actions,
        'retained_actions': retained_actions,
        'elapsed_seconds': round(perf_counter() - start, 3),
    }
    if any(layers[i] != EXPECTED_BY_OCCUPANCY[i] for i in range(max_stones+1)):
        raise AssertionError('independent raw BFS occupancy count disagrees')
    if max_stones == 5 and (candidate_actions != 88193892 or retained_actions != 17724120):
        raise AssertionError('independent raw BFS transition count disagrees')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='Independent raw-state 5x5 Quixo reachability verifier')
    parser.add_argument('--max-stones', type=int, default=5)
    parser.add_argument('--max-states', type=int, default=2_500_000)
    args = parser.parse_args(argv)
    print(json.dumps(enumerate_raw(args.max_stones, max_states=args.max_states), sort_keys=True))


if __name__ == '__main__':
    main()
