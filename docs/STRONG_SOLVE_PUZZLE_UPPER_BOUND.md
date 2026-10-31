# Rigorous upper bound on 5x5 reachable forcing-win puzzles

## Exact counting contract

A puzzle here is a legally reachable, nonterminal 5x5 board-and-turn
state from which the player to move has a finite forcing-win strategy.
Square rotations/reflections D4 identify equivalent puzzles; colors
and the turn remain distinct. This is a mathematically specified
family, NOT a human-rated puzzle difficulty.

The exact reachable full-game puzzle count remains UNSOLVED.

## New relevant prior-art evidence

Tanaka, Bonnet, Tixeuil and Tamura (2020/2022), "Quixo Is Solved",
https://arxiv.org/pdf/2007.15895, Table 2, report an exact strong
solution on the normalized X-to-move 25-cell structural board space:

    WIN     441,815,157,309
    LOSS    279,746,227,956
    DRAW    125,727,224,178
    SUM     847,288,609,443 = 3^25

Their solver counts include structurally possible but historically
unreachable boards and terminal states. These are not puzzle counts.
A corresponding color/turn swap maps this table to O-to-move boards.

## Rigorous terminal correction

An X-to-move terminal WIN state has at least one X five-cell line,
even when both players have a line (in the both-line case the last
mover loses). For the 12 five-cell line masks, inclusion-exclusion
gives the exact terminal X-winning board count:

    T_X = SUM_{nonempty subsets A of 12 lines}
          (-1)^(|A|+1) * 3^(25 - |union_{L in A} L|)

The exact verified result is T_X=39,719,507,107. Therefore, after
removing terminal X-winning boards from the published total, the
number of structural nonterminal WIN boards with a fixed active
player is 402,095,650,202. Across two turns there are exactly
804,191,300,404 structural nonterminal WIN states; this still
includes unreachable boards.

## Tighter global ceiling using D4 symmetry

Every X-first legally reachable nonterminal board with at least
two marked cells has at least one X and at least one O. There are
only four exceptional reachable *D4 classes*: the empty root and
the three geometrically different X-only one-cube states.

For each of the seven nonidentity D4 transformations, count all
fixed structural nonterminal boards with both X and O by
inclusion-exclusion on 12 X/O terminal lines over the transformation's
cycle variables. The verified per-symmetry counts are:

    1616, 1149024, 1616, 9475712, 12622208, 9475712, 12622208

Their sum is 45,348,096. For the reachable both-colored winning-root
subset A, Burnside's lemma gives

    |A/D4| <= floor((804191300404 + 2 * 45348096)/8)
           = 100535249574.

Adding all four exceptional reachable monochrome classes
conservatively yields

    REACHABLE NONTERMINAL FORCING-WIN D4 PUZZLE CLASSES
    <= 100,535,249,578.

This is a mathematical upper bound conditional on the published
strong-solver WLD results, NOT an independently computed exact
reachable puzzle count. Every combinatorial step and the seven
nonidentity symmetry-fixed counts are checked locally in
tools/structural_winning_upper.py. Associated unit tests:
tests/test_structural_winning_upper.py.

The previous 192,103,543,264 remains an upper bound for ALL
reachable nonterminal positions, even those not forcing wins;
it should never be silently replaced with the WIN-only bound.

## How we move from a ceiling to an exact count

The cap-nine two-color exact bitset census in
tools/census5_dual_tier.cpp computes all geometrically unique,
legally reachable board-and-turn positions and their immediate
tactics, closing same-(X-count,O-count) cycles before advancing.
Full 0..25-cube reachability and deeper WDL classification remain
a major computational obligation. No claim of exact global
reachability or global WIN-class count is justified until every
relevant tier is exhausted and independently checked.
