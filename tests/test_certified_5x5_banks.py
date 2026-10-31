"""Full replay/proof/uniqueness/deduplication regression suite for 5x5 banks."""
from copy import deepcopy

import pytest

from quixoforge.model import Move, replay
from quixoforge.generator import certify
from quixoforge.catalog import generate_bank, verify_bank, verify_entry, bank_json, _identity
from quixoforge.game_counts import game_count_summary

# Prefix+partial suffix independently proven to be nonterminal and win next.
HISTORY = tuple(
    Move.parse(s) for s in (
        "24:U", "3:R", "2:R", "3:R", "1:R", "3:D", "5:U", "23:U"
    )
)


def sample_entry():
    doc = certify(HISTORY, 1, unique=False)
    state = replay(HISTORY)
    doc.update(orbit_id=_identity(state),
               board="".join("." if x == 0 else "X" if x == 1 else "O"
                             for x in state.cells),
               turn="X" if state.turn == 1 else "O")
    return doc


def test_known_legal_x_first_winning_root_reaudits():
    doc = sample_entry()
    assert doc["minimal_bound"] == 1
    assert verify_entry(doc, exact_horizon=True, unique=False) == doc["orbit_id"]


def test_forged_position_and_solution_cannot_enter_bank():
    clean = sample_entry()
    for key, bad in (
        ("board", "." * 25),
        ("orbit_id", "0" * 64),
        ("turn", "O"),
        ("solutions", []),
        ("history", ["0:R"] + clean["history"]),
        ("minimal_bound", 3),
        ("proof", {"outcome": "WIN", "move": "not_a_move", "child": {}}),
    ):
        broken = deepcopy(clean)
        broken[key] = bad
        with pytest.raises((ValueError, AssertionError, TypeError)):
            verify_entry(broken, exact_horizon=True, unique=False)


def test_bank_requires_complete_unique_reachable_certificate(monkeypatch):
    # Deterministic fixed source: the second requested puzzle must not be
    # an identical D4 orbit, even when history or sampling seed differ.
    import quixoforge.catalog as catalog
    base = sample_entry()
    monkeypatch.setattr(catalog, "generate", lambda **kwargs: deepcopy(base))
    bank = generate_bank(count=1, seed=7, depth=1, unique=False,
                         searches=2, attempts_per_search=1)
    assert verify_bank(bank) == 1
    assert bank_json(bank).count('"orbit_id"') == 1
    assert bank["puzzles"][0]["orbit_id"] == base["orbit_id"]
    with pytest.raises(LookupError, match="only 1 of 2"):
        generate_bank(count=2, seed=7, depth=1, unique=False,
                      searches=2, attempts_per_search=1)
    forged = deepcopy(bank)
    forged["puzzles"].append(deepcopy(forged["puzzles"][0]))
    forged["requested"] = 2
    forged["generated"] = 2
    with pytest.raises(ValueError, match="duplicate"):
        verify_bank(forged)


def test_generator_rejects_shorter_than_advertised_depth(monkeypatch):
    import quixoforge.catalog as catalog
    monkeypatch.setattr(catalog, "generate", lambda **kwargs: sample_entry())
    with pytest.raises(LookupError):
        generate_bank(count=1, seed=12, depth=3, unique=False, searches=2,
                      attempts_per_search=1)


def test_parameter_bounds_and_boolean_type_checks():
    with pytest.raises(ValueError):
        generate_bank(count=True, seed=1)
    with pytest.raises(ValueError):
        generate_bank(count=1, seed=1, searches=0)
    with pytest.raises(ValueError):
        generate_bank(count=1, seed=1, exact_horizon=1)


def test_game_counts_retain_independent_scopes():
    data = game_count_summary()
    assert data["complete_winning_move_sequences"]["cardinality"] == "countably_infinite"
    assert data["complete_winning_move_sequences"]["exact"] is True
    assert data["reachable_board_turn_positions"]["global_exact"] is None
    assert data["reachable_board_turn_positions"]["nonterminal_orbits_k8"] == 75401235
    assert data["certified_forcing_win_position_puzzles"]["known_distinct_lower_bound"] == 5435153
    assert data["certified_forcing_win_position_puzzles"]["unique_first_action_known_lower_bound"] == 1942980
    assert data["human_meaningful_puzzles"]["global_exact"] is None
