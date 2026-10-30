"""Separate graph- and Burnside-based census verifier.

Unlike census.py, this implementation never groups states by canonical keys:
each qualifying state contributes its D4 stabilizer weight, divided by eight.
It obtains game values from an independently reconstructed bitboard graph,
then checks every packed-tablebase value against that graph.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .retrograde import Outcome, solve, verify
from .tablebase import Tablebase
from .variants import VariantBits, VariantBitboard, initial
from .reachability import ReachabilityIndex
from .model import X
from . import bitboard


def _rotated(x, o, turn, k):
    """Independent geometric rotation THEN reflection, unlike census.py."""
    a = b = 0
    for index in range(9):
        r, c = divmod(index, 3)
        for _ in range(k % 4):
            r, c = c, 2 - r
        if k >= 4:
            c = 2 - c
        j = r * 3 + c
        a |= ((x >> index) & 1) << j
        b |= ((o >> index) & 1) << j
    return a, b, turn


def _result_counters(graph, game):
    raw = defaultdict(Counter)
    weighted_horizons = defaultdict(Counter)
    for s, outcome in graph.outcomes.items():
        stabilizer = sum(_rotated(s.x, s.o, s.turn, k) == (s.x, s.o, s.turn) for k in range(8))
        assert stabilizer in (1, 2, 4, 8)
        orbit_size = 8 // stabilizer
        for k in range(8):
            transformed = VariantBits(*_rotated(s.x, s.o, s.turn, k), size=3)
            if transformed not in graph.outcomes:
                raise AssertionError("graph not closed under geometric symmetry")
            if graph.outcomes[transformed] != outcome or graph.remoteness.get(transformed) != graph.remoteness.get(s):
                raise AssertionError("value not symmetry-equivariant")
        chosen = []
        rem = graph.remoteness.get(s)
        if game.winner(s) is not None:
            chosen.append("terminal")
        else:
            chosen.append("P0_nonterminal")
            children = [(move, game.apply(s, move)) for move in game.legal_moves(s)]
            if outcome == Outcome.WIN:
                chosen.append("P1_forced_win")
                winning = [(m, child) for m, child in children if graph.outcomes[child] == Outcome.LOSS]
                if not winning:
                    raise AssertionError("WIN without action")
                fastest_distance = min(graph.remoteness[child] for _, child in winning)
                if len(winning) == 1:
                    chosen.append("P2_unique_win")
                    if rem >= 3 and len(game.legal_moves(winning[0][1])) >= 2:
                        chosen.append("P4_unique_nontrivial_reply")
                else:
                    chosen.append("multiple_winning_actions")
                if sum(graph.remoteness[child] == fastest_distance for _, child in winning) == 1:
                    chosen.append("unique_fastest_win")
                weighted_horizons["P1_remoteness"][str(rem)] += stabilizer
                if len(winning) == 1:
                    weighted_horizons["P2_remoteness"][str(rem)] += stabilizer
            elif outcome == Outcome.LOSS:
                chosen.append("forced_loss")
                if sum(graph.remoteness[child] == rem - 1 for _, child in children) == 1:
                    chosen.append("unique_max_delay")
        for family in chosen:
            raw[family][orbit_size] += 1
    families = {}
    for family, sizes in sorted(raw.items()):
        if any(count % size for size, count in sizes.items()):
            raise AssertionError("nonintegral D4 orbit partition")
        families[family] = {
            "orbits": sum(count // size for size, count in sizes.items()),
            "raw_states": sum(sizes.values()),
            "orbit_size_hist": {str(size): count // size for size, count in sorted(sizes.items())},
        }
    hist = {}
    for family, values in weighted_horizons.items():
        if any(v % 8 for v in values.values()):
            raise AssertionError("nonintegral Burnside horizon classes")
        hist[family] = {k: v // 8 for k, v in sorted(values.items(), key=lambda kv: int(kv[0]))}
    return families, hist


def verify_3x3() -> dict:
    """Fully reconstruct bitboard graph, classify and compare every reported family."""
    game = VariantBitboard(3)
    start = VariantBits.from_state(initial(3))
    exact = solve(game, start, max_states=40_000)
    verify(game, exact)
    table = Tablebase.load()
    if len(exact.outcomes) != table.states:
        raise AssertionError("tablebase graph size disagrees")
    for state, kind in exact.outcomes.items():
        key = (state.x, state.o, state.turn)
        actual = table._entries.get(key)
        if actual is None or actual.outcome != kind or actual.remoteness != exact.remoteness.get(state):
            raise AssertionError(f"tablebase disagrees at state {key}")
    families, hist = _result_counters(exact, game)
    fixed_sum = sum(sum(_rotated(s.x, s.o, s.turn, k) == (s.x, s.o, s.turn)
                        for s in exact.outcomes) for k in range(8))
    if fixed_sum % 8:
        raise AssertionError("Burnside integrality")
    independently_counted = {
        "reachable_states": len(exact.outcomes),
        "legal_transitions": exact.edge_count,
        "outcomes": dict(Counter(x.value for x in exact.outcomes.values())),
        "orbit_count_all": fixed_sum // 8,
        "burnside_fixed_sum": fixed_sum,
        "families": families,
        "orbit_remoteness_hist": hist,
        "initial_outcome": exact.outcome(start).value,
        "initial_remoteness": exact.remoteness[start],
    }
    from .census import census_3x3
    observed = census_3x3(table)
    for k, v in independently_counted.items():
        if observed[k] != v:
            raise AssertionError(f"independent 3x3 census mismatch for {k}: {observed[k]} != {v}")
    return observed


def _rotate5(state, k):
    """Independent coordinate transformation for fixed-start 5x5 positions."""
    cells = [0] * 25
    for i, v in enumerate(state.cells):
        r, c = divmod(i, 5)
        for _ in range(k % 4):
            r, c = c, 4-r
        if k >= 4:
            c = 4-c
        cells[r*5+c] = v
    return tuple(cells), state.turn


def verify_5x5_sparse(max_stones: int = 3) -> dict:
    if type(max_stones) is not int or max_stones not in (0,1,2,3,4):
        raise ValueError("max_stones must be 0..4")
    reachable = ReachabilityIndex.build(max_stones, start=X)
    states = set(reachable._parents)
    hist = defaultdict(Counter)
    candidate_edges = inside_edges = 0
    fixed_sum = 0
    for state in states:
        occupancy = (25 - state.cells.count(0))
        bs = bitboard.Bits.from_state(state)
        if bitboard.winner(bs) is not None:
            raise AssertionError("unexpected 5x5 win in occupancy <=4")
        legal = bitboard.legal_moves(bs)
        candidate_edges += len(legal)
        for action in legal:
            if occupancy == max_stones and state.cells[action.index] == 0:
                continue
            child = bitboard.apply(bs, action).state()
            if child not in states:
                raise AssertionError("restricted graph not transition-closed")
            inside_edges += 1
        stab = sum(_rotate5(state,k) == (state.cells,state.turn) for k in range(8))
        if stab not in (1,2,4,8):
            raise AssertionError("invalid orbit stabilizer")
        fixed_sum += stab
        hist[str(occupancy)][8 // stab] += 1
    orbit_count = fixed_sum // 8
    if fixed_sum % 8 or any(v % size for sizes in hist.values() for size,v in sizes.items()):
        raise AssertionError("5x5 orbit integrality")
    by_occupancy = {
        k: {"states": sum(sizes.values()),
            "orbits": sum(count // size for size, count in sizes.items()),
            "nonterminal_states": sum(sizes.values()),
            "nonterminal_orbits": sum(count // size for size, count in sizes.items())}
        for k, sizes in sorted(hist.items())
    }
    from .census import census_5x5_sparse
    observed = census_5x5_sparse(max_stones)
    expected = {
        "reachable_states": len(states),
        "candidate_transitions_examined": candidate_edges,
        "in_domain_edges": inside_edges,
        "orbit_count_all": orbit_count,
        "nonterminal_orbits": orbit_count,
        "nonterminal_states": len(states),
        "by_occupancy": by_occupancy,
        "burnside_fixed_sum": fixed_sum,
    }
    for key, value in expected.items():
        if observed[key] != value:
            raise AssertionError(f"independent 5x5 sparse mismatch for {key}: {observed[key]} != {value}")
    return observed


def verify_census(size: int = 3, max_stones: int = 3):
    if size == 3:
        return verify_3x3()
    if size == 5:
        return verify_5x5_sparse(max_stones)
    raise ValueError("census supports only complete 3x3 or 5x5 occupancy<=3")
