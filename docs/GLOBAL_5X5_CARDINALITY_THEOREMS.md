# Global 5x5 Quixo counts: exact theorems versus puzzle-census gaps

Three distinct mathematical objects must not be confused: complete ordered
winning game histories, winning terminal board states, and nonterminal
intellectual puzzles.

## Theorem A — exactly countably infinite legal winning histories

A history is an ordered list of legal 5x5 two-player Quixo actions starting
from the empty X-first board and stopping at its first winner. Actions specify
a perimeter cube (row-major index 0..24) and an insertion endpoint L/R/U/D.

Construct the legal move sequences:
- P = [24:U, 3:R]
- C = [3:R, 3:R]
- W = [2:R, 3:R, 1:R, 3:D, 5:U, 23:U, 23:U].

After P, the top row is ...XO, side to move X. Both moves in C are legal
and nonterminal, and they return *the entire board and turn* to that state.
W then reaches an X-winning top row XXXXX for the first time.

For every n >= 0, P + C repeated n times + W is a distinct legal first-win
history with length 9 + 2n. This injects natural numbers into winning
histories. Every legal history is a finite word over a finite alphabet,
so there are no more than countably many. Thus the exact cardinality is
ALEPH-NULL (countably infinite). Executable independent replay:
tests/test_winning_histories_infinite.py.

This does not imply infinitely many distinct board-position puzzles.

## Theorem B — exact structural terminal configurations across all 25 cubes

Ignore physical-game reachability temporarily. Each of the 25 cells may be
blank, X, or O. A terminal board contains an all-X or all-O 5-cell row,
column or long diagonal (12 line masks in all). D4 symmetry preserves
colors and turn. Applying inclusion-exclusion to the two color events
for each winning line, followed by Burnside over the eight D4 elements,
produces the exact counts below.

| Structural object | Exact count |
| --- | ---: |
| All terminal boards, without symmetry | 78,872,109,854 |
| Terminal board-and-turn states, without symmetry | 157,744,219,708 |
| Terminal board D4 orbits | 9,860,698,038 |
| Terminal board-and-turn D4 orbits | 19,721,396,076 |

Proof computation: tools/terminal_orbit_bounds.cpp.
An independent brute-force board-coloring enumerator verifies every
non-identity D4 fixed-board count (all 7 symmetry types). A third
algorithm, a five-row transfer-state dynamic program in
tools/terminal_row_transfer_oracle.py, separately derives precisely
768,416,499,589 raw no-winning-line boards and 768,368,824,944
nonterminal raw boards having both X and O, confirming the identity
symmetry term without using inclusion-exclusion. These counts
include unreachable boards and are NOT an exact number of games or
legally reachable terminal puzzles.

## Theorem C — stronger global upper bound for playable puzzle positions

For every *legally reachable nonterminal* position with at least two
colored cubes, both players have at least one mark. The first X action
adds X, and O's first action must add O because O cannot select X.
Neither count ever decreases. The only possible reachable nonterminal
monochrome orbits are empty X-first (one orbit) and X-only occupancy
one (three geometric orbits).

The same inclusion-exclusion calculation, restricted to nonterminal
colorings with both X and O present, gives exactly 192,103,543,260
structural board-and-turn D4 classes. Adding the four possible
monochrome reachable classes yields

    REACHABLE NONTERMINAL PUZZLE CLASS COUNT <= 192,103,543,264

for standard X-first 5x5 Quixo, under D4 geometry (no color swap).

## Certified tactical lower bound

Independent finite-domain reachability and tactical evaluation through
eight occupied cubes identify 698,588 geometric win-in-one classes. A
separate exact three-ply AND/OR search identifies 370 more disjoint
geometric forcing-win-by-three classes among roots with <=7 cubes.
Thus for the explicit property "legally reachable nonterminal positions
from which the player to move can force a terminal victory in finite time":

    698,958 <= FORCING-WIN POSITION D4 CLASSES <= 192,103,543,264

This is a rigorous interval, NOT an exact global total. Counting the
unknown remaining positions and longer tactics is an open computational
task. "Human meaningfulness" needs its own mathematical or empirical
criterion. No unqualified exact global finite "number of puzzles"
follows from a solved starting position or from board-coloring counts.

External prior work: Tanaka et al., Quixo Is Solved
https://arxiv.org/abs/2007.15895; Robert Shi (2024),
Parallel Solving of Two-Player Tierable Abstract Strategy Games,
https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-139.html.
