"""Exhaustive census regressions, independently derived orbit counts and falsifiers."""
from collections import Counter

import pytest

from quixoforge.model import Move
from quixoforge.retrograde import Outcome
from quixoforge.variants import VariantBits, VariantReference, initial
from quixoforge.tablebase import Tablebase
from quixoforge.census import (
    D4_3, canonical_key, census_3x3, census_5x5_sparse, key_of,
    maps3, records_3x3, transform_key, transform_move,
)
from quixoforge.census_verify import verify_3x3, verify_5x5_sparse


def test_exact_3x3_complete_independently_verified():
    report = verify_3x3()
    assert report["reachable_states"] == 32027
    assert report["legal_transitions"] == 276936
    assert report["orbit_count_all"] == 4433
    assert report["burnside_fixed_sum"] == 35464
    assert report["outcomes"] == {"WIN": 20247, "LOSS": 11780}
    expected = {
        "terminal": (11770, 1644),
        "P0_nonterminal": (20257, 2789),
        "P1_forced_win": (15167, 2062),
        "P2_unique_win": (1648, 212),
        "P4_unique_nontrivial_reply": (384, 48),
        "adaptive_response_win": (320, 40),
        "unique_fastest_win": (2768, 362),
        "multiple_winning_actions": (13519, 1850),
        "forced_loss": (5090, 727),
        "unique_max_delay": (432, 56),
    }
    for name, (raw, orbits) in expected.items():
        assert report["families"][name]["raw_states"] == raw
        assert report["families"][name]["orbits"] == orbits
    assert report["orbit_remoteness_hist"]["adaptive_response_win_remoteness"] == {"3": 26, "5": 10, "7": 4}
    assert report["orbit_remoteness_hist"]["P2_remoteness"] == {
        "1": 164, "3": 34, "5": 10, "7": 4
    }


def test_sparse_5x5_exact_independent_bitboard_verification():
    report = verify_5x5_sparse(3)
    assert report["reachable_states"] == 12297
    assert report["candidate_transitions_examined"] == 498328
    assert report["in_domain_edges"] == 59516
    assert report["nonterminal_orbits"] == 1576
    assert report["by_occupancy"] == {
        "0": {"states": 1, "orbits": 1, "nonterminal_states": 1, "nonterminal_orbits": 1},
        "1": {"states": 16, "orbits": 3, "nonterminal_states": 16, "nonterminal_orbits": 3},
        "2": {"states": 468, "orbits": 60, "nonterminal_states": 468, "nonterminal_orbits": 60},
        "3": {"states": 11812, "orbits": 1512, "nonterminal_states": 11812, "nonterminal_orbits": 1512},
    }


def test_3x3_orbit_transform_is_idempotent_not_color_swapped():
    root = key_of(initial(3))
    assert len(D4_3) == 8 == len(set(D4_3))
    assert canonical_key(root) == root
    key = (1, 0, -1)
    assert canonical_key(key) != canonical_key((0, 1, -1))
    assert canonical_key(key) != canonical_key((1, 0, 1))
    assert all(canonical_key(transform_key(key, m)) == canonical_key(key) for m in D4_3)
    with pytest.raises(ValueError):
        transform_key(key, (0,) * 9)
    with pytest.raises(ValueError):
        transform_key((1, 1, 1), D4_3[0])
    assert len(maps3()) == 8


def test_move_transform_covar_and_full_action_identity():
    game = VariantReference(3)
    tb = Tablebase.load()
    # Entire first-move set, including legal moves that can share a child,
    # must transform bijectively. Terminal positions have zero actions.
    for ix, (key, _) in enumerate(tb._entries.items()):
        if ix % 29:
            continue
        state = VariantBits(*key, size=3).state()
        legal = game.legal_moves(state)
        for m in D4_3:
            rotated = VariantBits(*transform_key(key, m), size=3).state()
            transformed = {transform_move(action, m) for action in legal}
            assert transformed == set(game.legal_moves(rotated))
            for action in legal:
                after = key_of(game.apply(state, action))
                expected = transform_key(after, m)
                actual = key_of(game.apply(rotated, transform_move(action, m)))
                assert expected == actual


def test_unique_puzzle_corpus_all_solutions_and_histories_replay():
    game = VariantReference(3)
    tb = Tablebase.load()
    unique = records_3x3("P2_unique_win")
    nontrivial = records_3x3("P4_unique_nontrivial_reply")
    adaptive = records_3x3("adaptive_response_win")
    assert len(unique) == 212
    assert len(nontrivial) == 48
    assert len(adaptive) == 40
    assert len({row["id"] for row in unique}) == len(unique)
    assert len({row["id"] for row in nontrivial}) == len(nontrivial)
    unique_ids = {row["board"] + row["turn"] for row in unique}
    assert all(row["board"] + row["turn"] in unique_ids for row in nontrivial)
    assert {r["board"] + r["turn"] for r in adaptive} <= {r["board"] + r["turn"] for r in nontrivial}
    for record in unique + nontrivial + adaptive:
        state = initial(3)
        for token in record["shortest_legal_history"]:
            state = game.apply(state, Move.parse(token))
        board = "".join("." if v == 0 else "X" if v == 1 else "O" for v in state.cells)
        assert board == record["board"]
        assert ("X" if state.turn == 1 else "O") == record["turn"]
        choices = [m for m in game.legal_moves(state)
                   if tb.lookup(game.apply(state, m)).outcome == Outcome.LOSS]
        assert len(choices) == 1
        assert record["solutions"] == [str(choices[0])]
        assert record["remoteness"] == tb.lookup(state).remoteness


def test_reject_invalid_domain_or_family():
    with pytest.raises(ValueError, match="occupancy cap"):
        census_5x5_sparse(5)
    with pytest.raises(ValueError, match="occupancy cap"):
        census_5x5_sparse(-1)
    with pytest.raises(ValueError, match="unsupported objective"):
        records_3x3("undefined")


def test_sparse_5x5_four_stone_exact_new_domain():
    report = verify_5x5_sparse(4)
    assert report["reachable_states"] == 199461
    assert report["candidate_transitions_examined"] == 7945716
    assert report["in_domain_edges"] == 1253304
    assert report["orbit_count_all"] == 25235
    assert report["burnside_fixed_sum"] == 201880
    assert report["by_occupancy"]["4"] == {
        "states": 187164, "orbits": 23659,
        "nonterminal_states": 187164, "nonterminal_orbits": 23659,
    }
