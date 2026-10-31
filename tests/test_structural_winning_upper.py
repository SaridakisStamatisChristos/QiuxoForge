"""Independent mathematical proof-regressions for 5x5 forcing-win ceiling."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from structural_winning_upper import calculate, fixed_nonterminal_both_colors, x_terminal_boards
from quixoforge.game_counts import game_count_summary


def test_published_wld_and_independent_terminal_combinatorics():
    r = calculate()
    assert sum(r["published_one_turn_WLD"].values()) == 3**25
    assert x_terminal_boards() == 39_719_507_107
    assert r["structural_W_nonterminal_states_both_turns"] == 804_191_300_404
    assert r["reachable_forcing_win_D4_orbits_upper_bound"] == 100_535_249_578
    assert r["kind"] == "upper_bound_not_exact_reachable_count"


def test_nonidentity_symmetry_fixed_cases_and_model_constraints():
    expected = [1616, 1149024, 1616, 9475712, 12622208, 9475712, 12622208]
    assert [fixed_nonterminal_both_colors(g) for g in range(1,8)] == expected


def test_count_api_preserves_exact_versus_upper_bound_semantics():
    counts=game_count_summary()
    assert counts["certified_forcing_win_position_puzzles"]["structural_upper_bound"] == 100_535_249_578
    assert counts["reachable_board_turn_positions"]["global_nonterminal_orbit_upper_bound"] == 192_103_543_264
    assert counts["certified_forcing_win_position_puzzles"]["global_exact"] is None
