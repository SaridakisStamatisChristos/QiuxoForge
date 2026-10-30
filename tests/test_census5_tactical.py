"""Regression checks for the exact real-board 5x5 immediate tactical census."""
import pytest

from quixoforge.census5_tactical import (
    census, orbit_bfs, history_of, canonical_with_transform, transform_key,
)
from quixoforge.model import initial, Move, replay
from quixoforge import reference


def test_complete_5x5_five_cube_census_and_independent_winning_oracle():
    result, records = census(5, verify=True, emit="unique_win_in_one")
    assert result["reachable_states"] == 2_254_843
    assert result["d4_position_orbits"] == 283_316
    assert result["positions_by_occupancy"]["5"] == {
        "states": 2_055_382, "d4_orbits": 258_081,
    }
    assert result["win_in_one"] == {"raw_states": 936, "d4_orbits": 120}
    assert result["unique_win_in_one"] == {"raw_states": 360, "d4_orbits": 46}
    assert result["win_actions_per_orbit"] == {
        "1": 46, "2": 4, "3": 30, "4": 10, "5": 14, "7": 8, "8": 8,
    }
    assert result["position_orbits_by_size"] == {
        "1": 1, "2": 13, "4": 2900, "8": 280402,
    }
    assert len(records) == 46
    assert len({row["id"] for row in records}) == 46
    for row in records:
        history = tuple(Move.parse(s) for s in row["shortest_legal_history"])
        state = replay(history)
        assert reference.winner(state) is None
        assert "".join("." if v == 0 else "X" if v == 1 else "O"
                       for v in state.cells) == row["board"]
        choices = [
            m for m in reference.legal_moves(state)
            if reference.winner(reference.apply(state, m)) == state.turn
        ]
        assert len(choices) == 1
        assert row["solutions"] == [str(choices[0])]


def test_zero_to_four_stone_domains_have_no_immediate_tactics():
    result, records = census(0, verify=True, emit="win_in_one")
    assert result["reachable_states"] == 1
    assert result["win_in_one"]["d4_orbits"] == 0
    assert records == []


def test_reject_invalid_5x5_reachability_domains_and_non_d4_transform():
    for cap in (-1, 6, True, 5.2):
        with pytest.raises(ValueError):
            orbit_bfs(cap)
    for k in (-1, 8, True):
        with pytest.raises(ValueError):
            transform_key((0, 0, 1), k)
    with pytest.raises(ValueError):
        census(5, emit="unproved_long_win")
    assert canonical_with_transform((0, 0, 1))[0] == (0, 0, 1)


def test_standalone_5x5_cli(capsys):
    import json
    from quixoforge.census5_tactical import main
    main(["--max-stones", "0"])
    assert json.loads(capsys.readouterr().out)["reachable_states"] == 1
