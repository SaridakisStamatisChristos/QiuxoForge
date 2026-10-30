"""Independent exact row-transfer DP: all 5x5 boards without any completed line.

This is intentionally unrelated to the inclusion-exclusion/Burnside
implementation. No QuixoForge modules required. Counts all structural boards
without asking whether a board is legally reachable.
"""
from collections import defaultdict
from itertools import product


def count_nonterminal_boards() -> tuple[int, int]:
    # Track the common color in five column prefixes and two diagonals:
    # 0 = no longer capable of being a monochromatic winning line,
    # 1 = X still possible, 2 = O still possible.
    rows = [
        r for r in product((0, 1, 2), repeat=5)
        if r != (1,)*5 and r != (2,)*5
    ]
    states = {(None, 0): 1}
    for i in range(5):
        after = defaultdict(int)
        for (previous, seen), multiplicity in states.items():
            for row in rows:
                if previous is None:
                    current = tuple(row) + (row[i], row[4-i])
                else:
                    current = tuple(
                        old if old == mark else 0
                        for old, mark in zip(previous[:5], row)
                    ) + (
                        previous[5] if previous[5] == row[i] else 0,
                        previous[6] if previous[6] == row[4-i] else 0,
                    )
                colors = seen | (1 if 1 in row else 0) | (2 if 2 in row else 0)
                after[(current, colors)] += multiplicity
        states = after

    nonterminal = sum(
        n for (track, flags), n in states.items()
        if not any(track)
    )
    both = sum(
        n for (track, flags), n in states.items()
        if not any(track) and flags == 3
    )
    assert nonterminal == 768416499589
    assert both == 768368824944
    return nonterminal, both


if __name__ == "__main__":
    a, b = count_nonterminal_boards()
    print(f"structural_nonterminal_boards={a}")
    print(f"structural_nonterminal_boards_both_colors={b}")
