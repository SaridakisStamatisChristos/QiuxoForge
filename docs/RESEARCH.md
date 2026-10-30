# Formal game model and research notes

## Source of rules and scope

Gigamic, *QUIXO Rules of the Game*, March 2017, English section, page 4, https://export.gigamic.com/wp-content/uploads/2021/01/INS-RULES_QUIXO_03-2017.pdf . Only the **two-player** variant is implemented. The official four-player team rules require oriented point markings and asymmetric teammate selection. They are not equivalent to a two-player game with four turn-taking players.

## Position

A position is `(cells, turn)` where `cells ∈ {empty, X, O}^25` in row-major order, and `turn ∈ {X, O}`. Initial position is all empty, either starting player, default X. A `Move(i, edge)` selects perimeter index `i` with value empty or `turn`, then shifts the contiguous row/column along the path from `i` to the chosen extremity `edge` such that `path[j] <- old(path[j+1])` and `path[last] <- turn`. The selected cube cannot be returned to its original position. `turn` then flips. No move is legal from a terminal state.

A horizontal/vertical/diagonal line of five identical nonblank marks wins, with 12 potential lines. If a move leaves winning lines of *both* symbols, **the mover loses**. Because `turn` is flipped immediately after a move, a both-line terminal position's winner is `turn`. A single-line position is won by the marked player. This winner function assumes the terminal board is being interpreted as the result of the immediately preceding mover; standalone arbitrary boards without a replay witness may not be reachable.

### Boundary: legal-state validation

`State` checks shape, value domain, side-to-move, and immutability. This is *structural* validation, NOT historical reachability. `replay(history)` establishes constructive reachability because every attempted move is checked, and a trace continuing after a win is rejected. `validate_history(target, history)` verifies the exact witness. Arbitrary standalone positions may be structurally valid but impossible to reach; solvers accept them only under the caller's explicit assumption that the board is meaningful. Deciding reachability without a witness is NOT implemented.

### Proven invariant: 44 opening moves

Four corners admit exactly two different insertion extremities each. The 12 remaining perimeter cells admit exactly three. All 16 perimeter cells are initially blank. Thus `4*2 + 12*3 = 44` legal opening moves. The code exhaustively enumerates these and all their legal second moves in tests.

### Proven invariant: no nonterminal blocked position

If a nonterminal state had no legal move for player P, every perimeter cube would have the opposing symbol (empty and P cubes are always selectable at the perimeter). Its top row, a subset of the perimeter, would then consist entirely of the opponent's marks, contradicting the state being nonterminal. Thus the no-move/no-pass ambiguity cannot occur on a nonterminal 5x5 two-player position under this model.

### Proven invariant: nonblank occupancy never decreases

A legal move selects either an empty cube (reinserted with a mark; occupancy +1) or a cube already bearing the mover's symbol (reinserted still bearing that symbol; occupancy unchanged). Shifting is a permutation of the remaining cubes. In particular, the number of each player's marks never decreases; its own turn increases by at most one and the other player's turn does not alter that count.

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
2. Full arbitrary-board reachability (especially terminal simultaneous-line boards) without a legal move history.
3. Verified performance improvement: D4 saves nodes on symmetric positions but canonicalization has overhead. Benchmark results depend on workload and hardware; validate speed with wider sampled positions and run-to-run variance.
4. Formal machine-checked proof of source-level transition equivalence/invariants, e.g. a separate Lean model or independently extracted specification.
5. Four-player team point orientation and correct player/team turn-order semantics, implemented as a separate game variant if requested.

No AI-generated statement in this document is represented as a proof-assistant-verified theorem.
