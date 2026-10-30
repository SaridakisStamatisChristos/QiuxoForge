"""Exhaustive exact <=3-ply forced-win classifier on real 5x5 roots with <=5 marks.

The SEARCH ROOT is occupancy-restricted and proved reachable. All tactical
continuations are UNRESTRICTED in occupancy: no truncation of defender moves.
The memoized threat preimages are algebraic translations of all 44 legal
insertions, not probabilistic heuristics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import json

from .model import X, Move
from .bitboard import LINE_MASKS, PATHS
from .census5_tactical import _apply, _winner, orbit_bfs, transform_key

# Preimage of each winning row/column/diagonal after each insertion.
# For cells shifted into the hole, the source is the next cell along the
# extraction-to-insertion path. The final insertion cell is always our mark.
# A winning line need not include the insertion point; retain all 12 lines.
_TEMPLATE = []
for move, path in PATHS.items():
    previous = {dest: source for dest, source in zip(path, path[1:])}
    required = tuple(
        sum(1 << previous.get(index, index)
            for index in range(25)
            if line & (1 << index) and index != path[-1])
        for line in LINE_MASKS
    )
    _TEMPLATE.append((move, path, sum(1 << p for p in path), required))


@lru_cache(maxsize=100_000)
def potential_winning_action_indices(own: int) -> tuple[int, ...]:
    """Complete superset of direct wins, before ownership/dual-win filtering."""
    if type(own) is not int or own < 0 or own >= (1 << 25):
        raise ValueError("invalid player mask")
    if own.bit_count() < 4:
        return ()
    return tuple(i for i, (_, _, _, required) in enumerate(_TEMPLATE)
                 if any(own & mask == mask for mask in required))


def immediate_win_indices(state: tuple[int, int, int]) -> tuple[int, ...]:
    x, o, turn = state
    if _winner(state) is not None:
        return ()
    own, enemy = (x, o) if turn == X else (o, x)
    return tuple(
        i for i in potential_winning_action_indices(own)
        if not (enemy & (1 << _TEMPLATE[i][0].index))
        and _winner(_apply(state, _TEMPLATE[i][1], _TEMPLATE[i][2])) == turn
    )


def forcing_first_indices_three(state: tuple[int, int, int]) -> tuple[int, ...]:
    """All first actions that guarantee victory on or before the third ply.

    Does NOT use a bounded-occupancy graph for tactical continuation.
    Terminal consequences are evaluated after each move.
    """
    x, o, turn = state
    if _winner(state) is not None:
        return ()
    own = x if turn == X else o
    if own.bit_count() < 3:
        return immediate_win_indices(state)
    enemy = o if turn == X else x
    occupied = x | o
    forcing = []
    for i, (move, path, mask, _) in enumerate(_TEMPLATE):
        if enemy & (1 << move.index):
            continue
        # Two remaining attacker turns can create at most two marks.
        if own.bit_count() == 3 and occupied & (1 << move.index):
            continue
        after_first = _apply(state, path, mask)
        first_result = _winner(after_first)
        if first_result == turn:
            forcing.append(i)
            continue
        if first_result == -turn:
            continue
        defender_enemy = after_first[0] if turn == X else after_first[1]
        forced = True
        for defend_move, defend_path, defend_mask, _ in _TEMPLATE:
            if defender_enemy & (1 << defend_move.index):
                continue
            after_defense = _apply(after_first, defend_path, defend_mask)
            result = _winner(after_defense)
            if result == turn:
                continue  # defender has already lost by terminal rule
            if result == -turn or not immediate_win_indices(after_defense):
                forced = False
                break
        if forced:
            forcing.append(i)
    return tuple(forcing)


def census_three(*, verify: bool = False) -> dict:
    """Complete 5x5 K<=5 D4-quotient census for forced wins by ply three."""
    graph = orbit_bfs(5)
    analyzed = 0
    by_k = Counter()
    forced3 = forced3_raw = exact3 = exact3_raw = 0
    unique_exact3 = unique_exact3_raw = 0
    for key in graph:
        own = key[0] if key[2] == X else key[1]
        if own.bit_count() < 3:
            continue
        analyzed += 1
        k = (key[0] | key[1]).bit_count()
        by_k[k] += 1
        actions = forcing_first_indices_three(key)
        if not actions:
            continue
        stab = sum(transform_key(key, g) == key for g in range(8))
        orbit_size = 8 // stab
        forced3 += 1
        forced3_raw += orbit_size
        immediate = immediate_win_indices(key)
        if not immediate:
            exact3 += 1
            exact3_raw += orbit_size
            if len(actions) == 1:
                unique_exact3 += 1
                unique_exact3_raw += orbit_size
        if verify:
            from . import reference
            from .census5_tactical import _state
            position = _state(key)
            # Independent reference all-first-action check for each positive.
            for first in reference.legal_moves(position):
                child = reference.apply(position, first)
                first_win = reference.winner(child)
                brute = first_win == position.turn or (
                    first_win is None and all(
                        reference.winner(reference.apply(child, defense)) == position.turn
                        or (
                            reference.winner(reference.apply(child, defense)) is None
                            and any(
                                reference.winner(reference.apply(
                                    reference.apply(child, defense), reply
                                )) == position.turn
                                for reply in reference.legal_moves(reference.apply(child, defense))
                            )
                        )
                        for defense in reference.legal_moves(child)
                    )
                )
                if brute != (_TEMPLATE.index(next(t for t in _TEMPLATE if t[0] == first)) in actions):
                    raise AssertionError("reference forcing-action disagreement")
    return {
        "schema": 1,
        "domain": "5x5 X-first roots occupancy<=5; unrestricted 3-ply continuations",
        "reachable_position_orbits": len(graph),
        "potentially_tactical_root_orbits": analyzed,
        "potential_roots_by_occupancy": dict(sorted(by_k.items())),
        "forced_win_by_3": {"orbits": forced3, "raw_states": forced3_raw},
        "exactly_3_not_1": {"orbits": exact3, "raw_states": exact3_raw},
        "unique_exactly_3": {"orbits": unique_exact3, "raw_states": unique_exact3_raw},
        "note": "3-ply finite-horizon result; not an unrestricted perfect-play value",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exact 5x5 forced-win-by-three census for K<=5 roots")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(census_three(verify=args.verify), sort_keys=True))


if __name__ == "__main__":
    main()
