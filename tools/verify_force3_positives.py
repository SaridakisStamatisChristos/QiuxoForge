"""Independent no-QuixoForge-import certification of every 5x5 exactly-three-ply
positive produced by tools/census5_force3_native.cpp.

Reads 'F3|x|o|turn_bit|forcing_first_actions|orbit_size' lines from the
native solver's stderr. Uses separately written list-shift/move/terminal
semantics, never the native bitboard masks or threat-preimage algorithm.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import json
from pathlib import Path


def terminal(state):
    board, turn = state
    lines = [board[5*r:5*r+5] for r in range(5)]
    lines += [tuple(board[r*5+c] for r in range(5)) for c in range(5)]
    lines += [tuple(board[6*i] for i in range(5)),
              tuple(board[4+4*i] for i in range(5))]
    has_x = any(all(v == 1 for v in line) for line in lines)
    has_o = any(all(v == -1 for v in line) for line in lines)
    return turn if has_x and has_o else 1 if has_x else -1 if has_o else None


def moves(state):
    board, turn = state
    if terminal(state) is not None:
        return ()
    out = []
    for i, mark in enumerate(board):
        r, c = divmod(i, 5)
        if (r not in (0, 4) and c not in (0, 4)) or mark not in (0, turn):
            continue
        if c: out.append((i, "L"))
        if c < 4: out.append((i, "R"))
        if r: out.append((i, "U"))
        if r < 4: out.append((i, "D"))
    return tuple(out)


def apply(state, move):
    board, turn = state
    i, edge = move
    r, c = divmod(i, 5)
    step = {"L": -1, "R": 1, "U": -5, "D": 5}[edge]
    length = {"L": c, "R": 4-c, "U": r, "D": 4-r}[edge]
    shifted = list(board)
    for t in range(length):
        shifted[i + t * step] = board[i + (t+1) * step]
    shifted[i + length * step] = turn
    return tuple(shifted), -turn


@lru_cache(maxsize=400_000)
def immediate_win(state):
    actor = state[1]
    for move in moves(state):
        if terminal(apply(state, move)) == actor:
            return True
    return False


def forcing_moves(state):
    if terminal(state) is not None:
        return ()
    actor = state[1]
    results = []
    for first in moves(state):
        after = apply(state, first)
        who = terminal(after)
        if who == actor:
            results.append(first)
            continue
        if who is not None:
            continue
        still_forced = True
        for defense in moves(after):
            middle = apply(after, defense)
            result = terminal(middle)
            if result == actor:
                continue
            if result is not None or not immediate_win(middle):
                still_forced = False
                break
        if still_forced:
            results.append(first)
    return tuple(results)


def maps():
    mappings = []
    for reflect in (False, True):
        for quarter_turns in range(4):
            mp = []
            for cell in range(25):
                row, col = divmod(cell, 5)
                if reflect:
                    col = 4-col
                for _ in range(quarter_turns):
                    row, col = col, 4-row
                mp.append(5*row+col)
            mappings.append(tuple(mp))
    if len(set(mappings)) != 8:
        raise AssertionError("invalid independent D4")
    return tuple(mappings)


def transform(state, mapping):
    board, turn = state
    new_board = [0] * 25
    for i, dest in enumerate(mapping):
        new_board[dest] = board[i]
    return tuple(new_board), turn


def verify(source: Path) -> dict:
    representatives = []
    for line in source.read_text(encoding="utf8").splitlines():
        if not line.startswith("F3|"):
            continue
        fields = line.split("|")
        if len(fields) != 6:
            raise AssertionError("bad native root emission")
        representatives.append(tuple(map(int, fields[1:])))
    if len(representatives) != 370:
        raise AssertionError(f"expected 370 positive root orbits, got {len(representatives)}")
    transformations = maps()
    seen = set()
    hist = Counter()
    adaptive_hist = Counter()
    raw = 0
    for number, (x, o, turn_bit, expected_actions, claimed_orbit_size) in enumerate(representatives, 1):
        if x & o or (x | o).bit_count() != 7 or turn_bit not in (0, 1):
            raise AssertionError("invalid emitted board")
        board = tuple(1 if x & (1 << i) else -1 if o & (1 << i) else 0
                      for i in range(25))
        state = board, (-1 if turn_bit else 1)
        if terminal(state) is not None or immediate_win(state):
            raise AssertionError("exactly-three-ply candidate already terminal or winning in one")
        choices = forcing_moves(state)
        if not choices or len(choices) != expected_actions:
            raise AssertionError(f"independent full AND/OR result disagrees on candidate {number}")
        orbit = {transform(state, g) for g in transformations}
        if len(orbit) != claimed_orbit_size:
            raise AssertionError("D4 multiplicity disagrees")
        representative = min(orbit)
        if representative in seen:
            raise AssertionError("duplicate geometric root")
        seen.add(representative)
        raw += len(orbit)
        hist[len(choices)] += 1
        # Defender-dependent-response objective: two distinct defender
        # moves force disjoint winning final-action sets. Do not equate
        # different resulting boards with distinct action identities.
        adaptive = False
        for first in choices:
            after = apply(state, first)
            sets = []
            for defense in moves(after):
                middle = apply(after, defense)
                if terminal(middle) == state[1]:
                    continue  # defender already lost under terminal rules
                winning_replies = frozenset(
                    m for m in moves(middle)
                    if terminal(apply(middle, m)) == state[1]
                )
                if not winning_replies:
                    raise AssertionError("previously certified force3 action has uncovered defense")
                if any(winning_replies.isdisjoint(old) for old in sets):
                    adaptive = True
                    break
                sets.append(winning_replies)
            if adaptive:
                break
        if adaptive:
            adaptive_hist[len(choices)] += 1
        if number % 50 == 0:
            print(f"verified {number}/370 independent full-branch certificates", flush=True)
    if sum(adaptive_hist.values()) != 370 or adaptive_hist != hist:
        raise AssertionError("new defender-dependent solution classification disagrees")
    if raw != 2880 or hist[1] != 64:
        raise AssertionError("raw total or unique-first-action classes disagree")
    result = {
        "schema": 1, "variant": "5x5 X-first, K=7 root, unrestricted 3-ply continuation",
        "exactly_three_orbits": len(seen), "raw_state_weight": raw,
        "unique_forcing_first_action_orbits": hist[1],
        "forcing_first_action_histogram": dict(sorted(hist.items())),
        "adaptive_reply_orbits": sum(adaptive_hist.values()),
        "adaptive_unique_first_action_orbits": adaptive_hist[1],
        "adaptive_forcing_first_action_histogram": dict(sorted(adaptive_hist.items())),
        "independent_oracle": "pure tuple array move/terminal AND-OR; no native source imports",
    }
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description="Independent 5x5 native forced-win-3 candidate auditor")
    ap.add_argument("--native-log", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args(argv)
    result = verify(args.native_log)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
