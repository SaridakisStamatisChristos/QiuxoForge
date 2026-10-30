# Formal game model and research notes

## Source of rules and scope

Gigamic, *QUIXO Rules of the Game*, March 2017, English section, page 4, https://export.gigamic.com/wp-content/uploads/2021/01/INS-RULES_QUIXO_03-2017.pdf . Both the **two-player** and **four-player** variants are implemented separately. Four-player team rules require oriented point markings and asymmetric teammate selection; they are not equivalent to a two-player game with four turn-taking players.

## Position

A position is `(cells, turn)` where `cells ∈ {empty, X, O}^25` in row-major order, and `turn ∈ {X, O}`. Initial position is all empty, either starting player, default X. A `Move(i, edge)` selects perimeter index `i` with value empty or `turn`, then shifts the contiguous row/column along the path from `i` to the chosen extremity `edge` such that `path[j] <- old(path[j+1])` and `path[last] <- turn`. The selected cube cannot be returned to its original position. `turn` then flips. No move is legal from a terminal state.

A horizontal/vertical/diagonal line of five identical nonblank marks wins, with 12 potential lines. If a move leaves winning lines of *both* symbols, **the mover loses**. Because `turn` is flipped immediately after a move, a both-line terminal position's winner is `turn`. A single-line position is won by the marked player. This winner function assumes the terminal board is being interpreted as the result of the immediately preceding mover; standalone arbitrary boards without a replay witness may not be reachable.

### Boundary: legal-state validation

`State` checks shape, value domain, side-to-move, and immutability. This is *structural* validation, NOT historical reachability. `replay(history)` establishes constructive reachability because every attempted move is checked, and a trace continuing after a win is rejected. `validate_history(target, history)` verifies the exact witness. Arbitrary standalone positions may be structurally valid but impossible to reach; solvers accept them only under the caller's explicit assumption that the board is meaningful. **An exact exhaustive reachability index is implemented for boards with at most three marked cubes, for a fixed starting player.** Positions with more marked cubes are explicitly `OUT_OF_SCOPE` for this index, never classified unreachable.

### Proven invariant: 44 opening moves

Four corners admit exactly two different insertion extremities each. The 12 remaining perimeter cells admit exactly three. All 16 perimeter cells are initially blank. Thus `4*2 + 12*3 = 44` legal opening moves. The code exhaustively enumerates these and all their legal second moves in tests.

### Proven invariant: no nonterminal blocked position

If a nonterminal state had no legal move for player P, every perimeter cube would have the opposing symbol (empty and P cubes are always selectable at the perimeter). Its top row, a subset of the perimeter, would then consist entirely of the opponent's marks, contradicting the state being nonterminal. Thus the no-move/no-pass ambiguity cannot occur on a nonterminal 5x5 two-player position under this model.

### Proven invariant: nonblank occupancy never decreases

A legal move selects either an empty cube (reinserted with a mark; occupancy +1) or a cube already bearing the mover's symbol (reinserted still bearing that symbol; occupancy unchanged). Shifting is a permutation of the remaining cubes. In particular, the number of each player's marks never decreases; its own turn increases by at most one and the other player's turn does not alter that count.

## Exact low-occupancy reachability theorem and observed enumeration

**Finite-domain completeness.** Let `C(s)` be the number of occupied cubes in state `s`. Every legal move selects a blank cube or one already bearing the mover's mark. The path shift preserves the other cube values and the reinserted cube is marked by the mover. Hence `C(next) - C(s) ∈ {0,1}`. For any fixed start `s0` and any target `t` with `C(t) <= K`, every prefix state along any legal path from `s0` to `t` must also have occupancy <= K. Therefore a complete breadth-first exploration of the subgraph with occupancy <= K is sufficient **and necessary** for reachability decisions in that target domain, even with arbitrary cycles and unbounded move counts. BFS parent links provide *shortest histories* by the standard nonnegative unit-edge BFS invariant. This is a mathematical proof about the transition model; it is **not** a proof-assistant or source-code correctness proof.

`ReachabilityIndex.build(K, start=X|O)` exhaustively explores that finite domain without a depth cutoff, retaining complete state (25 cells and player to move), not quotienting by symmetry when producing histories. The two-player terminal rule is respected (no successors after a win). We constrain `K` to 0–3 to avoid unbounded memory/runtime costs. For `K=3`, there are at most `2 * sum_{i=0}^3 C(25,i) * 2^i = 39,302` structurally possible `(board,turn)` pairs; all 12,297 reachable states were independently re-enumerated with a separate bitboard breadth-first algorithm. They comprise 1,576 distinct D4 geometric orbits. The longest shortest legal history among these 12,297 states is 18 plies; **bounded-depth search to 3 plies would miss some reachable 3-mark states**.

| Cap K | Reachable states per fixed starter | Examined legal transitions |
|---|---:|---:|
| 0 | 1 | 44 |
| 1 | 17 | 704 |
| 2 | 485 | 20,012 |
| 3 | 12,297 | 498,328 |

Counts are reproducible by `test_three_stone_complete_index_matches_independent_bitboard_graph` and `test_witness_shortest_path_matches_bitboard_bfs_distance`; transition counts include paths whose resulting occupancy exceeds the cap and are pruned from the search queue. Reachability counts apply to each specified starter, not a union over the two. `X` and `O` starters have equal counts due to the color/turn renaming symmetry, which is separate from geometric D4 reduction.

## Exact bounded proof semantics

For depth `d` in **plies** and player to move `p`:

- Terminal: `WIN` if winner is `p`, else `LOSS`.
- Nonterminal `d=0`: `UNKNOWN` (never infer draw or loss).
- For `d>0`: `WIN` if there exists a legal child with `LOSS` at `d-1`; `LOSS` if *all* legal children have `WIN` at `d-1`; `UNKNOWN` otherwise.

This is a sound constructive AND/OR proof of a forced decisive outcome within `d` plies. `UNKNOWN` means not certified at this bound, not an actual game-theoretic draw. `ReferenceSolver` memoizes untransformed `State` keys and shifts Python lists. `BitboardSolver` uses separate 25-bit X/O masks and its own transitions, with geometric D4 canonicalized transpositions. The two implementations share the immutable representation of `Move` and the notion of D4 geometric transforms; their legal move and state-transition paths are independent. Tested covariance of all legal moves under all 8 D4 actions is empirical, not a formally checked theorem of the source code.

## Proof certificate verifier

`proof.produce` creates a finite AND/OR proof object with terminal leaves only:

- `WIN`: one listed legal move and a `LOSS` child.
- `LOSS`: **every** available legal move and a `WIN` child, with exact equality of move sets required.
- Terminal leaf: winner must exactly match the claimed `WIN`/`LOSS` perspective.

`proof.verify` independently applies reference rules to verify the proof tree. It does not consult solver caches, certificates' claimed hashes, or the optimized search. Puzzle audit additionally independently computes the entire winning first-move set with both search algorithms and verifies minimal forcing horizon (within the chosen bound). The JSON examples contain complete witness trees and histories, and `python -m quixoforge.verify_examples` rechecks them.

### Tactical difficulty

`immediate` is minimal bound 1; `short-forcing` is minimal bound 2 or 3; `deep-forcing` is minimal bound 4+. These labels are formal search-horizon classes, **not** tested human difficulty predictions. A depth-3 puzzle can be easier for a human than a depth-1 puzzle; no cognitive/psychometric claims are made.

## Remaining research gaps

1. Repetition/draw conventions and proof of the complete game-theoretic value from the starting position. The official rules do not supply a finite repetition draw rule in the cited two-player description; one must not invent it silently.
2. Arbitrary-board reachability with >=4 marked cubes (especially terminal simultaneous-line boards) without a legal move history. Extend the occupancy-complete index carefully with memory/cost budgets or new proof-based pruning.
3. Verified performance improvement: D4 saves nodes on symmetric positions but canonicalization has overhead. Benchmark results depend on workload and hardware; validate speed with wider sampled positions and run-to-run variance.
4. Formal machine-checked proof of source-level transition equivalence/invariants, e.g. a separate Lean model or independently extracted specification.
5. Four-player human consultation/tournament protocols are social controls and deliberately excluded from the engine. Four-player oriented points and seat progression are now implemented in both `teams` and `team_bitboard`.

No AI-generated statement in this document is represented as a proof-assistant-verified theorem.

## Four-player team model (v1.0)

A four-player position is `(point[25], seat, ply)`; `point ∈ {-1,0,1,2,3}` where `-1` is a blank cube and any other value indicates a marked cube pointing toward the numbered physical seat (north/east/south/west clockwise). `point=0/2` denotes X/team-even and `point=1/3` denotes O/team-odd. `seat = ply mod 4`, and the teammates are 0/2 and 1/3.

For `ply < 4` (first round), only blank cubes may be extracted; otherwise a cube may be extracted iff blank or `point == seat`. The selected perimeter cube may be shifted toward any *other* end of its row/column. The reinserted mark points either to the current seat or its opposite teammate. If no cube is selectable and the position is not terminal, a compulsory pass advances `seat`, leaving the board fixed. A terminal board is final and has no successors. Winner for a double-line terminal position is the team whose seat is next: the preceding mover's opposing team wins.

The optimized four-player model retains four disjoint 25-bit seat-pointer masks and shifts their contents with a separate algorithm. The geometric D4 transformations of the two-player board are **not blindly copied** to the four-player game: a reflection reverses seating orientation relative to clockwise turn order, and even rotations would require synchronized transforms of seat identities and the phase. Consequently four-player search uses direct hashed keys `(four masks, seat, min(ply,4))` and never claims an unsafe D4 quotient. All solver values remain bounded as in the two-player rules.

## Practical opponent / heuristic horizon (v1.0)

`AlphaBetaEngine` computes exact negamax for a **chosen finite depth using a heuristic leaf evaluation**. This is not an exact Quixo game-theoretic value. A position's static heuristic sums open line potential with weights `[0,2,12,80,650,5000]` and excludes opponent-contested rows; both-ended lines, direct terminal wins/losses and double-line precedence are handled by the terminal oracle before evaluating. Alpha-beta pruning is sound for the finite-depth negamax objective, and D4 transposition keys include depth and bound type (`LOWER/UPPER/EXACT`). The stored best action is in canonical coordinates and is transformed back on a cache hit. Only completely finished iterative-deepening depths are exposed as recommendations when the node budget is exhausted.

A separate independent reference minimax with no pruning checks the same fixed-depth *heuristic objective* for selected workloads. This proves equality of the sampled results, not strength superiority. See `engine_bench` for exact parameters and scores validated before timing.

## Game-agnostic proof trees and four-player tactical examples

`generic_proof.produce` and `generic_proof.verify` use only the `FiniteGame` protocol and `str(move)` as unambiguous action identifiers. For a `WIN` certificate they verify one legal winning branch recursively; for `LOSS` certificates they compare the complete reply-key set against every legal action and verify every branch. A terminal leaf is checked against the winner reported by the selected game model; no outcome is certified from a nonterminal horizon-zero leaf. The four-player generator uses `BitboardFourPlayerGame` to produce a certificate and the independent list-based `FourPlayerGame` to verify it. `team_puzzles.check` also recomputes the complete first-move solution set with both models and verifies minimal proven horizon.

For a forced pass, the singleton action is `PASS`, and the universal branch must include it. The fixture `examples/team_forcing_one.json` is a replayable witness of a four-seat tactical win at depth 1 with two winning point-direction choices; it is **not** claimed to have a unique first action. The two-player fixtures are independently verified by `verify_examples`.


## Exact loopy game solving and 3x3 verification (v1.1)

A finite graph is built by BFS from the legal empty-board opening. It includes all distinct `(board,player-to-move)` states, each action edge (duplicates retained), and all reachable terminals. Any `max_states` truncation raises and makes no claims about an incomplete graph. Exhaustive retrograde propagation starts at terminal game results and applies the monotone attractor equations:

- WIN iff some child is LOSS; choose fastest WIN, remoteness = 1 + min distance among LOSS children.
- LOSS iff every child is WIN; optimal loss delay = 1 + max distance among WIN children.
- NONFORCED iff it is in the complement of both finite attractors: it has no LOSS child but at least one NONFORCED child, so indefinite avoiding play is possible. It is **not** a forced terminal draw under the printed Quixo rules, which contain no repetition rule.

A priority queue keyed by distance ensures shortest winning strategies and longest delaying losing strategies are recorded in propagation order; the independent `verify` procedure checks the complete move graph and every local Bellman equation. These equations with strict distance descent on winning branches and universal closure on losing branches inductively establish every decisive label. Remaining states have an avoiding successor and are never mislabeled terminal wins/losses. The finite completeness claim is over the computed 32,027 reachable 3x3 board/turn states, **not** the 5x5 game.

For the 3x3 variant, reference tuple-shift and independently implemented occupancy-mask moves were run to closure. Their complete reachable sets, directed edges, winner evaluations, outcome labels and remotenesses agreed position by position. The initial state is a seven-ply WIN and there are **20,247 WIN / 11,780 LOSS / zero NONFORCED** states. It reproduces published 3x3 results (Shi 2024); it does not establish novelty. The tablebase is 7-byte binary records (`<HHbBB`), sorted by `(X mask,O mask,turn)`, prefixed by `QF3\x01` and a count, gzip-compressed with a fixed timestamp and SHA256 integrity check. Data can be regenerated using `python -m quixoforge.tablebase --rebuild`. The static compressed data is installed with the Python wheel.

**Prior art:** [Tanaka et al., *Quixo Is Solved* (2020)](https://arxiv.org/abs/2007.15895) solved 5x5 as a draw. [Robert Shi, *Parallel Solving of Two-Player Tierable Abstract Strategy Games* (2024)](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-139.pdf), section 7.4, independently reproduced 5x5 and reported 32,027 reachable 3x3 positions with a first-player win in 7. The earlier README's suggestion that 5x5 opening remains an open research result was wrong and is withdrawn. QuixoForge's own independent full 5x5 strong solve remains unattempted due to resources, not because the answer is unknown.
