# Exact two-color monotone decomposition of the full 5×5 Quixo puzzle census

## Theorem: both mark counts are individually monotone

Let (s) be any legal 5×5 two-player Quixo position and write (x(s))
and (o(s)) for its numbers of X-marked and O-marked cubes. Let (s\to s')
be a legal move by player (p\in\{X,O\}). Every move selects only a
**blank cube or the moving player's own cube**, shifts a row/column,
and reinserts that selected cube marked as (p). Thus

- if a blank cube was selected, the mover's mark count increases by one;
- if a marked own cube was selected, both mark counts remain unchanged;
- the opponent's mark count never changes on this move.

Formally,
[
(x(s'),o(s'))=(x(s),o(s))+\delta e_p,\quad\delta\in\{0,1\}.
]
A terminal winning board stops play and has no outgoing legal actions.
Therefore the reachable graph is **monotone in each color**, not merely
in total occupancy. This statement is a mathematical invariant of the
specified rules, not a benchmark extrapolation.

## Exact layer-saturation recurrence

Define (R_{a,b}) as the set of legally reachable **board-plus-turn**
positions with exactly (a) X marks and (b) O marks, including terminal
positions but never expanding from a terminal. Let (E^0_{a,b}) denote
all legal actions that preserve both counts (select an owned mark), and
let (E^+_{a,b}) denote actions that add one mark of the mover.

For each ((a,b)), seeds consist of the empty X-first board if
((a,b)=(0,0)), plus all one-mark-increasing children produced by
previously saturated (R_{a-1,b}) and (R_{a,b-1}). Then

[
 R_{a,b}=\operatorname{Reach}_{E^0_{a,b}}(\operatorname{Seeds}_{a,b}).
]

Here (operatorname{Reach}_{E^0}) is the complete fixed-point closure,
including every finite number of mark-preserving moves; all seeds are
also included. Terminal states are retained as reached but not expanded.

**Proof:** Every history to ((a,b)) has nondecreasing mark counts.
Consider the *last* mark-increasing move. Its source must be one of the
two predecessor lattice cells. After that move, every further move
preserves both counts, and is included in the closure. Conversely,
every seed and all its legal count-preserving descendants are
reachable by concatenating legal histories. Strong induction on
(a+b\) proves the recurrence for all ((a,b)) with (a+b\le25).

No DAG claim is made for the individual fixed-count subgraphs: they
may contain genuine directed cycles, which is why fixed-point
saturation, not single-pass dynamic programming, is required.

## D4 quotient and exact puzzle classification

All eight square transformations preserve each player's mark count,
the side to move, legal shifts and terminal outcomes. Therefore
(R_{a,b}/D_4) is also saturated by the same recurrence. Count each
representative once with the orbit-stabilizer weight
(8/|\operatorname{Stab}(s)|). If the puzzle objective is a local
first-move property, independently check **every legal first action**,
including actions whose successor has one additional occupied cube.
Counting only in-scope successors would produce false negatives.

The recurrence partitions the full 25-cube problem into disjoint
colored occupancy strata and allows parallel processing of different
(a,b) pairs at the same total occupancy once predecessor strata
have been sealed. This is **exact**, regardless of how many
mark-preserving cycles occur.

## Out-of-core implementation contract (not yet executed globally)

1. Work in increasing (k=a+b); seal each pair only after saturation
   and cross-checking source-child membership.
2. Produce canonical keys including both colors and side to move.
   Deduplicate using the **complete key**; hashes alone are not exact.
3. Partition incoming seed streams deterministically by an exact key
   range or a hash shard with full-key comparison; preserve source
   provenance and checkpoint when a shard is sealed.
4. Saturate owned-cube transitions within a ((a,b)) pair until its
   queue is empty, including arbitrary cycles and terminal stopping.
5. Emit every blank-selection child to the correct successor
   ((a+1,b)) or ((a,b+1)) stream and classify all locally decidable
   first-move puzzle families.
6. Maintain a signed or hash-verified manifest of states/orbits per
   stratum, terminal counts, candidate edges and in-scope transitions,
   independent verifier evidence, and explicit process resource limits.
7. Restart interrupted strata only from validated checkpoints;
   never label unsealed strata complete or extrapolate counts.

This gives a mathematically correct **architecture** for an exact
global census, not a claim that all strata have already been computed
or that disk, CPU, or verification costs are negligible.

## Current evidence versus objective

The current 5×5 native program performs complete BFS with a scalar
occupied-cube cap and has been independently checked through K=7.
Its K=8 extension is presently a native-computed result with a
separate raw-state verifier being executed. The two-color recurrence
is a proof of a stronger decomposition, but a general out-of-core
implementation reaching all K=25 strata remains open.

No exact global number of subjectively *meaningful* puzzles exists
without choosing an explicit mathematical/human-rated criterion.
Unique immediate-winning actions are a precisely counted restricted
family, **not equivalent** to unique eventual winning strategies or
human cognitive difficulty.
