"""Exact, explicitly scoped Quixo puzzle census.

3x3 results use the complete X-first, terminal-stopped tablebase. Puzzles
are geometric D4 orbits of (rules, side to move, objective, state).
No arbitrary color swapping; legal actions (not distinct child boards) count.

The 5x5 computation is a COMPLETE occupancy<=4 reachability-domain census,
not a solution of the unrestricted 5x5 game.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from hashlib import sha256
import json

from .model import X
from .retrograde import Outcome
from .tablebase import Tablebase
from .variants import VariantBits, VariantReference, initial
from .reachability import ReachabilityIndex, occupancy
from . import reference, symmetry


FAMILIES = (
    "P0_nonterminal", "P1_forced_win", "P2_unique_win",
    "P4_unique_nontrivial_reply", "adaptive_response_win", "unique_fastest_win",
    "multiple_winning_actions", "forced_loss", "unique_max_delay",
    "terminal",
)


def maps3() -> tuple[tuple[int, ...], ...]:
    """Eight old-index to new-index maps for the square."""
    maps = []
    for reflection in (False, True):
        for turns in range(4):
            mapping = []
            for old in range(9):
                r, c = divmod(old, 3)
                if reflection:
                    c = 2 - c
                for _ in range(turns):
                    r, c = c, 2 - r
                mapping.append(3 * r + c)
            maps.append(tuple(mapping))
    assert len(set(maps)) == 8
    return tuple(maps)


D4_3 = maps3()


def transform_key(key: tuple[int, int, int], mapping: tuple[int, ...]) -> tuple[int, int, int]:
    """Transform both color masks; never alter the side to move."""
    if len(mapping) != 9 or set(mapping) != set(range(9)):
        raise ValueError("mapping must be a permutation of the 3x3 cells")
    x, o, turn = key
    VariantBits(x, o, turn, 3)
    nx = no = 0
    for i, j in enumerate(mapping):
        nx |= ((x >> i) & 1) << j
        no |= ((o >> i) & 1) << j
    return nx, no, turn


def canonical_key(key: tuple[int, int, int]) -> tuple[int, int, int]:
    return min(transform_key(key, m) for m in D4_3)


def transform_move(move, mapping):
    """Apply geometric symmetry to an insertion-edge action, not just its cube."""
    from .model import Move
    r, c = divmod(move.index, 3)
    end = {"L": 3*r, "R": 3*r+2, "U": c, "D": 6+c}[move.edge]
    source, target = mapping[move.index], mapping[end]
    sr, sc = divmod(source, 3)
    er, ec = divmod(target, 3)
    if sr == er and ec == 0:
        edge = "L"
    elif sr == er and ec == 2:
        edge = "R"
    elif sc == ec and er == 0:
        edge = "U"
    elif sc == ec and er == 2:
        edge = "D"
    else:
        raise AssertionError("symmetry did not preserve the insertion edge")
    return Move(source, edge)


def key_of(state) -> tuple[int, int, int]:
    b = VariantBits.from_state(state)
    return b.x, b.o, b.turn


def _facts(key, entries, game):
    """Return exact action-count features. Every legal action is evaluated."""
    state = VariantBits(*key, size=3).state()
    terminal_winner = game.winner(state)
    if terminal_winner is not None:
        return {"terminal"}, (), (), 0, 0
    value = entries[key]
    actions = game.legal_moves(state)
    children = [(move, entries[key_of(game.apply(state, move))]) for move in actions]
    families = {"P0_nonterminal"}
    wins = ()
    fastest = ()
    if value.outcome == Outcome.WIN:
        families.add("P1_forced_win")
        wins = tuple(m for m, v in children if v.outcome == Outcome.LOSS)
        assert wins and value.remoteness is not None
        shortest = min(v.remoteness for _, v in children if v.outcome == Outcome.LOSS)
        assert shortest + 1 == value.remoteness
        fastest = tuple(m for m, v in children if v.outcome == Outcome.LOSS and v.remoteness == shortest)
        if len(wins) == 1:
            families.add("P2_unique_win")
            successor = game.apply(state, wins[0])
            if value.remoteness >= 3 and len(game.legal_moves(successor)) >= 2:
                families.add("P4_unique_nontrivial_reply")
                # Check whether different opponent replies need incompatible
                # next winning actions; terminal reply blunders need no answer.
                responses = []
                for reply in game.legal_moves(successor):
                    next_state = game.apply(successor, reply)
                    if game.winner(next_state) is not None:
                        continue
                    answers = frozenset(
                        action for action in game.legal_moves(next_state)
                        if entries[key_of(game.apply(next_state, action))].outcome == Outcome.LOSS
                    )
                    if not answers:
                        raise AssertionError("forced-win reply without a winning response")
                    responses.append(answers)
                if any(a.isdisjoint(b) for i, a in enumerate(responses)
                       for b in responses[i+1:]):
                    families.add("adaptive_response_win")
        else:
            families.add("multiple_winning_actions")
        if len(fastest) == 1:
            families.add("unique_fastest_win")
    elif value.outcome == Outcome.LOSS:
        families.add("forced_loss")
        assert value.remoteness is not None
        assert children and all(v.outcome == Outcome.WIN for _, v in children)
        assert 1 + max(v.remoteness for _, v in children) == value.remoteness
        if sum(v.remoteness == value.remoteness - 1 for _, v in children) == 1:
            families.add("unique_max_delay")
    else:
        assert value.outcome == Outcome.NONFORCED
        assert value.remoteness is None
        assert any(v.outcome == Outcome.NONFORCED for _, v in children)
    return families, wins, fastest, len(actions), len({key_of(game.apply(state, m)) for m in actions})


def orbit_groups3(entries):
    groups = defaultdict(list)
    for key in entries:
        groups[canonical_key(key)].append(key)
    return groups


def census_3x3(tablebase: Tablebase | None = None) -> dict:
    """Full tablebase-backed classification, including exact geometric orbits."""
    tb = Tablebase.load() if tablebase is None else tablebase
    entries = tb._entries
    game = VariantReference(3)
    groups = orbit_groups3(entries)
    counts = defaultdict(Counter)
    horizons = defaultdict(Counter)
    for representative, members in groups.items():
        size = len(members)
        if size not in (1, 2, 4, 8):
            raise AssertionError("invalid orbit size")
        if set(members) != {transform_key(representative, m) for m in D4_3}:
            raise AssertionError("incomplete or contaminated D4 orbit")
        families, _, _, _, _ = _facts(representative, entries, game)
        for family in families:
            counts[family][size] += 1
        if "P1_forced_win" in families:
            horizon = str(entries[representative].remoteness)
            horizons["P1_remoteness"][horizon] += 1
            if "P2_unique_win" in families:
                horizons["P2_remoteness"][horizon] += 1
            if "adaptive_response_win" in families:
                horizons["adaptive_response_win_remoteness"][horizon] += 1

    fixed_sum = sum(
        sum(transform_key(key, m) == key for key in entries)
        for m in D4_3
    )
    if fixed_sum != 8 * len(groups):
        raise AssertionError("Burnside theorem discrepancy")
    result = {
        "schema": 1,
        "domain": "3x3 two-player X first complete reachable graph, stops at terminals",
        "reachable_states": tb.states,
        "legal_transitions": sum(len(game.legal_moves(VariantBits(*k, size=3).state())) for k in entries),
        "initial_outcome": tb.lookup(initial(3)).outcome.value,
        "initial_remoteness": tb.lookup(initial(3)).remoteness,
        "outcomes": dict(Counter(v.outcome.value for v in entries.values())),
        "orbit_count_all": len(groups),
        "burnside_fixed_sum": fixed_sum,
        "families": {
            family: {
                "orbits": sum(sizes.values()),
                "raw_states": sum(size * count for size, count in sizes.items()),
                "orbit_size_hist": {str(size): count for size, count in sorted(sizes.items())},
            } for family, sizes in sorted(counts.items())
        },
        "orbit_remoteness_hist": {
            family: dict(sorted(values.items(), key=lambda kv: int(kv[0])))
            for family, values in horizons.items()
        },
    }
    if sum(f["raw_states"] for name, f in result["families"].items() if name in ("P0_nonterminal", "terminal")) != tb.states:
        raise AssertionError("missing reachable states")
    return result


def census_5x5_sparse(max_stones: int = 3) -> dict:
    """Exact reachable structural-domain count, NOT 5x5 winning puzzles."""
    if type(max_stones) is not int or max_stones not in (0, 1, 2, 3, 4):
        raise ValueError("verified 5x5 census accepts occupancy cap 0..4")
    index = ReachabilityIndex.build(max_stones, start=X)
    groups = defaultdict(list)
    for state in index._parents:
        groups[symmetry.canonical(state)].append(state)
    strata = defaultdict(Counter)
    for _, members in groups.items():
        size = len(members)
        if size not in (1, 2, 4, 8):
            raise AssertionError("invalid 5x5 orbit")
        k = str(occupancy(members[0]))
        strata[k]["orbits"] += 1
        strata[k]["states"] += size
        if reference.winner(members[0]) is None:
            strata[k]["nonterminal_orbits"] += 1
            strata[k]["nonterminal_states"] += size
    fixed_sum = sum(sum(symmetry.transform(s, k) == s for s in index._parents) for k in range(8))
    if fixed_sum != len(groups) * 8:
        raise AssertionError("5x5 Burnside discrepancy")
    in_domain_edges = sum(
        1 for s in index._parents for m in reference.legal_moves(s)
        if occupancy(s) < max_stones or s.cells[m.index] != 0
    )
    return {
        "schema": 1, "domain": f"5x5 two-player X-first reachable occupancy <={max_stones} exhaustive",
        "reachable_states": index.state_count,
        "candidate_transitions_examined": index.examined_edges,
        "in_domain_edges": in_domain_edges,
        "orbit_count_all": len(groups),
        "nonterminal_orbits": sum(v["nonterminal_orbits"] for v in strata.values()),
        "nonterminal_states": sum(v["nonterminal_states"] for v in strata.values()),
        "by_occupancy": {k: dict(v) for k, v in sorted(strata.items())},
        "burnside_fixed_sum": fixed_sum,
    }


def _histories3():
    """Shortest legal X-first constructive reachability witnesses (BFS)."""
    game = VariantReference(3)
    root = initial(3)
    paths = {key_of(root): ()}
    todo = deque([root])
    while todo:
        state = todo.popleft()
        base = paths[key_of(state)]
        for move in game.legal_moves(state):
            nxt = game.apply(state, move)
            key = key_of(nxt)
            if key not in paths:
                paths[key] = base + (move,)
                todo.append(nxt)
    if len(paths) != 32027:
        raise AssertionError("history BFS incomplete")
    return paths


def records_3x3(family: str):
    """Return independently replayable geometric-unique puzzles for one family."""
    if family not in ("P1_forced_win", "P2_unique_win", "P4_unique_nontrivial_reply",
                      "adaptive_response_win", "unique_fastest_win", "unique_max_delay"):
        raise ValueError("unsupported objective family")
    entries = Tablebase.load()._entries
    game = VariantReference(3)
    histories = _histories3()
    records = []
    for key in sorted(orbit_groups3(entries)):
        families, wins, fastest, legal, successors = _facts(key, entries, game)
        if family not in families:
            continue
        state = VariantBits(*key, size=3).state()
        hist = histories[key]
        check = initial(3)
        for move in hist:
            check = game.apply(check, move)
        if check != state:
            raise AssertionError("bad reachability witness")
        if family == "unique_max_delay":
            actions = [(m, entries[key_of(game.apply(state,m))]) for m in game.legal_moves(state)]
            solutions = [m for m,v in actions if v.remoteness == entries[key].remoteness - 1]
        else:
            solutions = fastest if family == "unique_fastest_win" else wins
        # Resolve stabilizer ambiguity by canonicalizing the COMPLETE solution set.
        stabilizers = [m for m in D4_3 if transform_key(key, m) == key]
        canonical_solution = min(tuple(sorted(str(transform_move(m, g)) for m in solutions)) for g in stabilizers)
        board = "".join("." if v == 0 else "X" if v == X else "O" for v in state.cells)
        records.append({
            "schema": 1, "variant": "3x3-two-player-X-first",
            "id": f"QF3:{family}:{board}:{'X' if state.turn == X else 'O'}:r{entries[key].remoteness}",
            "objective": family, "board": board, "turn": "X" if state.turn == X else "O",
            "remoteness": entries[key].remoteness,
            "winning_actions": len(wins), "legal_actions": legal,
            "distinct_successors": successors, "solutions": list(canonical_solution),
            "shortest_legal_history": [str(m) for m in hist],
        })
    return records


def main(argv=None):
    ap = argparse.ArgumentParser(description="Exact Quixo puzzle census, no heuristic estimates")
    ap.add_argument("--size", type=int, choices=(3, 5), default=3)
    ap.add_argument("--max-stones", type=int, default=3)
    ap.add_argument("--family", choices=("P1_forced_win", "P2_unique_win",
                    "P4_unique_nontrivial_reply", "adaptive_response_win", "unique_fastest_win", "unique_max_delay"))
    ap.add_argument("--verify", action="store_true", help="run independent graph-and-symmetry verifier")
    args = ap.parse_args(argv)
    if args.family and args.size != 3:
        ap.error("individual certified puzzle records are available for 3x3 only")
    if args.family:
        for record in records_3x3(args.family):
            print(json.dumps(record, sort_keys=True))
    else:
        report = census_3x3() if args.size == 3 else census_5x5_sparse(args.max_stones)
        print(json.dumps(report, sort_keys=True))
    if args.verify:
        from .census_verify import verify_census
        verify_census(args.size, args.max_stones)


if __name__ == "__main__":
    main()
