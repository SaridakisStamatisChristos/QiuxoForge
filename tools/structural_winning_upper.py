"""Published strong-solve WLD totals + exact structural combinatorics.

A *bound* on legal nonterminal forcing-win D4 puzzle classes,
NOT the total number of reachable Quixo positions or a replacement
for the Tanaka et al. solver.

Tanaka, Bonnet, Tixeuil & Tamura, "Quixo Is Solved", 2020/22,
https://arxiv.org/abs/2007.15895 (Table 2).
All WLD counts are for one normalized side to move; the paper
identifies O-turn with color-swapped X-turn.
"""
from __future__ import annotations
from functools import lru_cache
import json

WIN, LOSS, DRAW = 441_815_157_309, 279_746_227_956, 125_727_224_178
LINES = (
    tuple(sum(1 << (5*r+c) for c in range(5)) for r in range(5))
    + tuple(sum(1 << (5*r+c) for r in range(5)) for c in range(5))
    + (sum(1 << (6*i) for i in range(5)), sum(1 << (4+4*i) for i in range(5)))
)

def x_terminal_boards() -> int:
    """Exact boards with at least one all-X line (O and blank both free)."""
    result = 0
    for subset in range(1, 1 << 12):
        required = 0
        for j, line in enumerate(LINES):
            if subset & (1 << j):
                required |= line
        result += (1 if subset.bit_count() & 1 else -1) * 3**(25-required.bit_count())
    return result

def _fixed_line_cycles(symmetry: int) -> tuple[int, tuple[int, ...]]:
    perm = []
    for cell in range(25):
        r, c = divmod(cell, 5)
        if symmetry >= 4:
            c = 4-c
        for _ in range(symmetry % 4):
            r, c = c, 4-r
        perm.append(5*r+c)
    ids = [-1]*25
    n = 0
    for cell in range(25):
        if ids[cell] != -1:
            continue
        j = cell
        while ids[j] == -1:
            ids[j] = n
            j = perm[j]
        n += 1
    masks = tuple(sum(1 << ids[cell] for cell in range(25) if line >> cell & 1)
                  for line in LINES)
    return n, masks

def fixed_nonterminal_both_colors(symmetry: int) -> int:
    """Exact D4-fixed nonterminal board count with X and O both present.

    Inclusion-exclusion covers each of the twelve X/O winning-line
    events, not a brute-force enumeration of 3^25 boards.
    """
    if type(symmetry) is not int or not 0 <= symmetry < 8:
        raise ValueError("symmetry must be a D4 index 0..7")
    n, masks = _fixed_line_cycles(symmetry)

    @lru_cache(None)
    def no_line(j: int, x: int, o: int) -> int:
        if j == 12:
            return 3 ** (n - (x | o).bit_count())
        line = masks[j]
        val = no_line(j+1, x, o)
        if not line & o:
            val -= no_line(j+1, x | line, o)
        if not line & x:
            val -= no_line(j+1, x, o | line)
        return val

    @lru_cache(None)
    def no_x_line_only(j: int, x: int) -> int:
        if j == 12:
            return 2 ** (n - x.bit_count())
        return (no_x_line_only(j+1, x)
                - no_x_line_only(j+1, x | masks[j]))

    return no_line(0, 0, 0) - 2*no_x_line_only(0, 0) + 1

def calculate() -> dict:
    assert WIN + LOSS + DRAW == 3**25
    x_terminal = x_terminal_boards()
    assert x_terminal == 39_719_507_107
    fixed = [fixed_nonterminal_both_colors(g) for g in range(1, 8)]
    assert fixed == [1616, 1149024, 1616, 9475712,
                     12622208, 9475712, 12622208]
    # One normalized side to move has exactly WIN structural WIN states.
    # Under official terminal rule, a terminal X-turn WIN state has an
    # X line, irrespective of whether O also has a line.
    w_nonterminal_two_turns = 2*(WIN-x_terminal)
    # For reachable nonterminal states with >=2 marks, both marks occur.
    # Hence all seven non-identity D4 fixed-point counts on these states
    # are bounded by 'fixed' for each turn. Burnside gives an integer
    # ceiling after floor division. At most four reachable monochrome
    # D4 classes (empty and X-only one-mark) are exceptional.
    bound = (w_nonterminal_two_turns + 2*sum(fixed))//8 + 4
    assert bound == 100_535_249_578
    return {
        "schema": 1,
        "source": "Tanaka et al. Quixo Is Solved Table 2 (arxiv:2007.15895)",
        "kind": "upper_bound_not_exact_reachable_count",
        "all_structural_boards_for_one_normalized_turn": 3**25,
        "published_one_turn_WLD": {"win":WIN, "loss":LOSS, "draw":DRAW},
        "structural_terminal_boards_with_X_line": x_terminal,
        "structural_W_nonterminal_states_both_turns": w_nonterminal_two_turns,
        "D4_nonidentity_fixed_nonterminal_both_colors": fixed,
        "reachable_forcing_win_D4_orbits_upper_bound": bound,
        "prior_upper_bound": 192_103_543_264,
        "caveat": "Requires the published strong-solving classification; no 5x5 global reachability count is asserted.",
    }

if __name__ == "__main__":
    print(json.dumps(calculate(), sort_keys=True))
