"""Explicit 5x5 count semantics: game histories vs positions vs puzzles.

Do not present a structural upper bound or partial occupancy census as the
exact global count of legally reachable puzzle positions.
"""
from __future__ import annotations

import json


def game_count_summary() -> dict:
    """Return reproducible, correctly scoped mathematical/census results.

    Exact complete game-history cardinality: countably infinite provided
    repeated nonterminal positions do not terminate play. A constructive
    two-ply cycle followed by a first win is independently replayable.
    """
    total_position_orbits_k8 = 75_434_676
    total_position_orbits_k9 = 316_462_989
    total_position_orbits_k10 = 1_113_552_661
    total_position_orbits_k11 = 3_332_049_627
    terminal_position_orbits_k8 = 33_441
    nonterminal_position_orbits_k8 = (
        total_position_orbits_k8 - terminal_position_orbits_k8
    )
    immediate_puzzles = 698_588
    three_ply_extra = 370
    unique_immediate = 243_957
    unique_three_ply_extra = 64
    return {
        "schema": 1,
        "variant": "standard_two_player_5x5_X_first",
        "identity": "D4_board_rotations_reflections; preserve_mark_colors_and_turn",
        "complete_winning_move_sequences": {
            "cardinality": "countably_infinite",
            "exact": True,
            "model": "finite move histories that end at first win; no repetition termination",
            "constructive_witness": {
                "prefix": ["24:U", "3:R"],
                "two_ply_cycle": ["3:R", "3:R"],
                "first_winning_suffix": [
                    "2:R", "3:R", "1:R", "3:D", "5:U", "23:U", "23:U",
                ],
                "winning_length_after_n_cycles": "9 + 2*n for any integer n>=0",
            },
        },
        "infinite_nonterminating_move_sequences": {
            "cardinality": "continuum",
            "cardinality_symbol": "2^(aleph_0)",
            "exact": True,
            "model": "infinite legal nonterminal move histories; no repetition termination",
            "constructive_witness": {
                "prefix": ["24:U", "3:R", "20:R", "20:R"],
                "binary_choice_cycles": [
                    ["3:R", "3:R"],
                    ["23:R", "23:R"],
                ],
                "proof": (
                    "both 2-ply cycles legally return to the same X-turn "
                    "nonterminal state; each infinite binary word yields "
                    "a distinct never-terminal game"
                ),
            },
        },
        "all_finite_and_infinite_legal_move_sequences": {
            "cardinality": "continuum",
            "exact": True,
            "caveat": "includes infinite nonterminating histories, not only games ending with a winner",
        },
        "reachable_board_turn_positions": {
            "global_exact": None,
            "global_status": "NOT_COMPUTED",
            "completely_enumerated_occupancy_at_most": 11,
            "independently_reproduced_through_occupancy": 8,
            "k11_verification_status": "single_engine_checkpointed_not_independently_replicated",
            "raw_states_k8": 603_033_221,
            "geometric_orbits_k8": total_position_orbits_k8,
            "raw_states_k9_cumulative": 2_530_588_373,
            "geometric_orbits_k9_cumulative": total_position_orbits_k9,
            "raw_states_k10_cumulative": 8_905_915_009,
            "geometric_orbits_k10_cumulative": total_position_orbits_k10,
            "raw_states_k11_exact_layer": 17_745_392_476,
            "geometric_orbits_k11_exact_layer": 2_218_496_966,
            "raw_states_k11_cumulative": 26_651_307_485,
            "geometric_orbits_k11_cumulative": total_position_orbits_k11,
            "raw_terminal_states_k11_cumulative": 117_842_292,
            "raw_terminal_states_k9_cumulative": 2_764_208,
            "nonterminal_orbits_k8": nonterminal_position_orbits_k8,
            "global_nonterminal_orbit_upper_bound": 192_103_543_264,
        },
        "certified_forcing_win_position_puzzles": {
            "global_exact": None,
            "global_status": "NOT_COMPUTED",
            "win_in_one_orbits_k8": immediate_puzzles,
            "win_in_one_orbits_k9_exact_layer": 4_736_195,
            "win_in_one_orbits_k9_cumulative": 5_434_783,
            "additional_forced_win_in_three_orbits_k7": three_ply_extra,
            "win_in_one_orbits_k10_cumulative": 31_939_126,
            "win_in_one_orbits_k11_exact_layer": 115_174_547,
            "win_in_one_orbits_k11_cumulative": 147_113_673,
            "known_distinct_lower_bound": 147_113_673 + three_ply_extra,
            "structural_upper_bound": 100_535_249_578,
            "upper_bound_source": (
                "Tanaka et al., Quixo Is Solved Table 2, minus exact structural "
                "terminal X-line boards, Burnside and fixed-both-color ceiling; "
                "tools/structural_winning_upper.py"
            ),
            "unique_win_in_one_orbits_k9_cumulative": 1_942_916,
            "unique_win_in_one_orbits_k10_cumulative": 11_527_844,
            "unique_win_in_one_orbits_k11_cumulative": 52_994_624,
            "k11_verification_status": "single_engine_checkpointed_not_independently_replicated",
            "unique_first_action_known_lower_bound": (
                52_994_624 + unique_three_ply_extra
            ),
            "note": (
                "Certifications are finite-horizon game-theoretic, not human "
                "difficulty assessments. Higher occupancies and longer "
                "forcing horizons are not globally enumerated beyond K11. K11 has a single exact engine plus checkpoint consistency checks, not an independent second enumeration."
            ),
        },
        "human_meaningful_puzzles": {
            "global_exact": None,
            "status": "UNDEFINED_WITHOUT_EXPLICIT_MEANINGFULNESS_CRITERION",
        },
        "reproduction": {
            "witness_test": "tests/test_winning_histories_infinite.py",
            "local_orbits_and_proofs": "docs/GLOBAL_5X5_CARDINALITY_THEOREMS.md",
            "finite_census": "docs/CENSUS_5X5_R7_V14.md",
            "k11_checkpointed_census": "docs/EXACT_K11_CHECKPOINTED_CENSUS.md",
        },
    }


def count_json() -> str:
    return json.dumps(game_count_summary(), sort_keys=True)
