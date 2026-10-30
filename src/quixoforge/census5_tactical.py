"""Exact 5x5 Quixo one-ply puzzle census over the complete reachable <=5-mark domain.

This is NOT a full game-theoretic 5x5 solution. An immediate winning
action is checked against the official terminal rule, and every legal
first action is considered. Only D4 geometry (never color swap) is used.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json

from .bitboard import LINE_MASKS, PATHS
from .model import Move, State, X, O, initial, replay
from . import reference, symmetry

Key = tuple[int, int, int]
# D4 permutations map an old row-major index to its transformed index.
_TABLES = tuple(
    tuple(
        tuple(sum(1 << mapping[offset + bit] for bit in range(min(8, 25 - offset))
                  if sample & (1 << bit))
              for sample in range(1 << min(8, 25 - offset)))
        for offset in (0, 8, 16, 24))
    for mapping in symmetry.D4
)
_ACTIONS = tuple((move, path, sum(1 << i for i in path))
                 for move, path in PATHS.items())


def _transform_mask(mask: int, g: int) -> int:
    chunks = _TABLES[g]
    return (chunks[0][mask & 255] |
            chunks[1][(mask >> 8) & 255] |
            chunks[2][(mask >> 16) & 255] |
            chunks[3][mask >> 24])


def transform_key(state: Key, g: int) -> Key:
    if type(g) is not int or not 0 <= g < 8:
        raise ValueError("D4 symmetry index must be 0..7")
    x, o, turn = state
    return _transform_mask(x, g), _transform_mask(o, g), turn


def canonical_with_transform(state: Key) -> tuple[Key, int]:
    return min((transform_key(state, g), g) for g in range(8))


def _apply(state: Key, path: tuple[int, ...], mask: int) -> Key:
    x, o, turn = state
    new_x, new_o = x & ~mask, o & ~mask
    for dst, src in zip(path, path[1:]):
        if x & (1 << src):
            new_x |= 1 << dst
        elif o & (1 << src):
            new_o |= 1 << dst
    if turn == X:
        new_x |= 1 << path[-1]
    else:
        new_o |= 1 << path[-1]
    return new_x, new_o, -turn


def _winner(state: Key) -> int | None:
    x, o, turn = state
    has_x = any(x & line == line for line in LINE_MASKS)
    has_o = any(o & line == line for line in LINE_MASKS)
    return turn if has_x and has_o else X if has_x else O if has_o else None


def orbit_bfs(max_stones: int = 5) -> dict[Key, tuple[Key, Move, int] | None]:
    """Complete orbit-quotient BFS including every same-occupancy cycle.

    A predecessor stores (canonical parent, parent's action, D4 map of child).
    The map also provides replayable shortest X-first histories. For a
    reachable position <=5 marks, terminal play cannot yet have occurred:
    each color must have acquired one mark before either can own five.
    """
    if type(max_stones) is not int or not 0 <= max_stones <= 5:
        raise ValueError("5x5 geometric BFS supports occupancy 0..5")
    root: Key = (0, 0, X)
    parents: dict[Key, tuple[Key, Move, int] | None] = {root: None}
    pending = deque([root])
    while pending:
        state = pending.popleft()
        x, o, turn = state
        filled = x | o
        occupancy = filled.bit_count()
        if _winner(state) is not None:
            raise AssertionError("unexpected terminal in occupancy<=5 reachable domain")
        for move, path, mask in _ACTIONS:
            if (o if turn == X else x) & (1 << move.index):
                continue
            if occupancy == max_stones and not filled & (1 << move.index):
                continue
            child, g = canonical_with_transform(_apply(state, path, mask))
            if child not in parents:
                parents[child] = (state, move, g)
                pending.append(child)
    return parents


def history_of(key: Key, parents: dict[Key, tuple[Key, Move, int] | None]) -> tuple[Move, ...]:
    """Shortest genuine X-first history to the canonical representative."""
    if key not in parents:
        raise ValueError("state is outside the enumerated reachable domain")
    reversed_steps: list[tuple[Move, int]] = []
    cursor = key
    while parents[cursor] is not None:
        parent, action, g = parents[cursor]
        reversed_steps.append((action, g))
        cursor = parent
    actions: tuple[Move, ...] = ()
    for move, g in reversed(reversed_steps):
        actions = tuple(symmetry.transform_move(action, g) for action in actions) + (
            symmetry.transform_move(move, g),)
    return actions


def _state(key: Key) -> State:
    x, o, turn = key
    return State(tuple(X if x & (1 << i) else O if o & (1 << i) else 0
                       for i in range(25)), turn)


def _winning_actions(key: Key) -> tuple[Move, ...]:
    x, o, turn = key
    # A winning insertion requires four existing marks of the moving color.
    if (x if turn == X else o).bit_count() < 4:
        return ()
    return tuple(
        move for move, path, mask in _ACTIONS
        if not (o if turn == X else x) & (1 << move.index)
        and _winner(_apply(key, path, mask)) == turn
    )


def census(max_stones: int = 5, *, verify: bool = False,
           emit: str | None = None) -> tuple[dict, list[dict]]:
    """Count ALL reachable positions and all first-move wins in the domain.

    emit: None, 'win_in_one', or 'unique_win_in_one'. Never returns
    uncertified arbitrary board setups.
    """
    if emit not in (None, "win_in_one", "unique_win_in_one"):
        raise ValueError("invalid one-ply objective")
    parents = orbit_bfs(max_stones)
    occupancy_orbits = Counter()
    occupancy_states = Counter()
    win_orbits = win_states = unique_orbits = unique_states = 0
    winning_action_hist = Counter()
    orbit_size_hist = Counter()
    output = []
    for key in sorted(parents):
        x, o, turn = key
        filled = x | o
        k = filled.bit_count()
        stabilizer = sum(transform_key(key, g) == key for g in range(8))
        if stabilizer not in (1, 2, 4, 8):
            raise AssertionError("invalid stabilizer")
        orbit_size = 8 // stabilizer
        occupancy_orbits[k] += 1
        occupancy_states[k] += orbit_size
        orbit_size_hist[orbit_size] += 1
        solutions = _winning_actions(key)
        if solutions:
            win_orbits += 1
            win_states += orbit_size
            winning_action_hist[len(solutions)] += 1
            if len(solutions) == 1:
                unique_orbits += 1
                unique_states += orbit_size
            if verify:
                # Independent tuple-array oracle checks EVERY first action,
                # not just the winning action(s), in every positive orbit.
                source = _state(key)
                oracle = tuple(m for m in reference.legal_moves(source)
                               if reference.winner(reference.apply(source, m)) == turn)
                if set(oracle) != set(solutions):
                    raise AssertionError(f"winning solution set mismatch: {key}")
                for g in range(8):
                    rotated = symmetry.transform(source, g)
                    transformed = {symmetry.transform_move(m, g) for m in solutions}
                    oracle_rotated = {
                        m for m in reference.legal_moves(rotated)
                        if reference.winner(reference.apply(rotated, m)) == turn
                    }
                    if transformed != oracle_rotated:
                        raise AssertionError("symmetry changed the puzzle solution set")
            if emit == "win_in_one" or (emit == "unique_win_in_one" and len(solutions) == 1):
                history = history_of(key, parents)
                source = _state(key)
                if replay(history) != source:
                    raise AssertionError("failed independent reachability replay")
                if any(reference.winner(reference.apply(source, m)) != turn for m in solutions):
                    raise AssertionError("failed independent winning move check")
                board = "".join("." if v == 0 else "X" if v == X else "O" for v in source.cells)
                family = "unique_win_in_one" if len(solutions) == 1 else "win_in_one"
                output.append({
                    "schema": 1, "id": f"QF5:{family}:{board}:{'X' if turn == X else 'O'}",
                    "variant": "5x5-X-first", "board": board,
                    "turn": "X" if turn == X else "O",
                    "objective": "win_on_next_move", "winning_actions": len(solutions),
                    "solutions": [str(m) for m in sorted(solutions)],
                    "shortest_legal_history": [str(m) for m in history],
                })
    report = {
        "schema": 1, "scope": f"5x5 X-first reachable occupancy<= {max_stones}; exact win in one only",
        "complete_domain": True,
        "reachable_states": sum(occupancy_states.values()),
        "d4_position_orbits": len(parents),
        "positions_by_occupancy": {
            str(i): {"states": occupancy_states[i], "d4_orbits": occupancy_orbits[i]}
            for i in range(max_stones + 1)
        },
        "position_orbits_by_size": {str(i): orbit_size_hist[i] for i in (1, 2, 4, 8)},
        "win_in_one": {"raw_states": win_states, "d4_orbits": win_orbits},
        "unique_win_in_one": {"raw_states": unique_states, "d4_orbits": unique_orbits},
        "win_actions_per_orbit": {str(k): v for k, v in sorted(winning_action_hist.items())},
        "epistemic_limit": "not an unrestricted 5x5 game solve or a global puzzle total",
    }
    if verify:
        for key, parent_data in parents.items():
            if parent_data is not None:
                parent, action, g = parent_data
                expected = canonical_with_transform(_apply(parent, PATHS[action],
                                               sum(1 << i for i in PATHS[action])))[0]
                if expected != key or transform_key(_apply(parent, PATHS[action],
                         sum(1 << i for i in PATHS[action])), g) != key:
                    raise AssertionError("inconsistent quotient reachability witness")
        if sum(i * orbit_size_hist[i] for i in (1, 2, 4, 8)) != report["reachable_states"]:
            raise AssertionError("D4 orbits do not partition the raw reachable states")
    return report, output


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Exact 5x5 Quixo one-ply tactical puzzle census")
    parser.add_argument("--max-stones", type=int, default=5)
    parser.add_argument("--family", choices=("win_in_one", "unique_win_in_one"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    report, records = census(args.max_stones, verify=args.verify, emit=args.family)
    if args.family:
        for record in records:
            print(json.dumps(record, sort_keys=True))
    else:
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
