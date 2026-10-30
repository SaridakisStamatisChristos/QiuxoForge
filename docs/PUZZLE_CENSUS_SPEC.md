# QuixoForge Puzzle Census — exact model and counting contract

## Game domain

The model is two-player Quixo, X starts from the empty board, all legal
histories stop when a winning terminal position is reached, and a side-to-move
is part of the state. The small 3x3 experimental variant requires three in
a row, while official 5x5 requires five. The non-repetition terminal-stopped
finite graph is used for exact WIN/LOSS/NONFORCED semantics. NONFORCED does
not invent an official arbitrary-repetition draw rule.

A puzzle is the tuple (rules variant, reachable nonterminal board/turn,
exact objective, legal first-action solution set, exact value/horizon).
The selected cube and insertion edge together form one distinct action.
Different actions with the same resulting state remain different solutions.

## Families for the **fully enumerated** 3x3 graph

- P0_nonterminal: reachable nonterminal state (research denominator).
- P1_forced_win: current player can force an eventual terminal win.
  Exactly the first actions leading to LOSS children are winning solutions.
- P2_unique_win: P1 with exactly one such winning action.
- P4_unique_nontrivial_reply: P2 with minimum forced-win remoteness
  >=3 plies, and at least two legal opponent replies after its winning move.
  This is a branch-complexity proxy, **not human-rated difficulty**.
- unique_fastest_win: exactly one winning action minimizes eventual forced-win
  remoteness; distinct from exactly one eventually winning action.
- multiple_winning_actions: P1 with at least two winning first actions.
- forced_loss: every legal action leads to a WIN child.
- unique_max_delay: forced_loss with exactly one first action maximizing
  the game-theoretically guaranteed loss delay.
- terminal: reachable already-won positions for denominator reconciliation;
  excluded from puzzles.

For WIN positions the minimal remoteness is one plus the minimum remoteness
of LOSS children; for LOSS positions it is one plus the maximum remoteness
of WIN children. No finite-depth UNKNOWN is relabeled as a draw.

## Mathematical equivalence

Only the eight D4 board symmetries are used by default. They preserve X/O
colors, side to move, selected cube and insertion edge, all legal choices,
winner precedence, objective, and entire winning solution sets. Color
swapping is forbidden in fixed X-start mode. Different objectives or
different variants are not identified. The canonical key for 3x3 is the
minimum lexicographic (X mask, O mask, turn) under the eight permutations.
The puzzle identity further records its family, variant and remoteness;
solution sets are stabilized when exporting a canonical representative.

Proof: each D4 transformation maps a board boundary and an insertion path
to another valid boundary and insertion path. Rotating/reflection of an
entire win line is another win line, including simultaneous-line winner
precedence. Thus applying a transformed action to a transformed state is
the transform of applying the original action. The empty board is fixed;
induction on history length gives D4-closure of the reachable state graph
with stop-after-win rules. Every listed family is invariant under these
automorphisms. Orbits have size 8 / |Stab(s)|. Burnside equivalently gives
the orbit count as (sum over all states of their stabilizer sizes) / 8.
Canonical grouping and stabilizer aggregation use distinct implementations.

## Exact domain limits and certification

The 3x3 census consumes a SHA256-verified full 32,027-state tablebase.
The independent checker builds and solves the complete bitboard game graph,
checks *all* tablebase state values and Bellman remotenesses, reconstructs
the first-action classification independently, and uses stabilizer-weight
counting instead of the producer's canonical-key grouping. Adversarial
tests cover false symmetry, color swaps, different turns, move-edge mapping,
reachability witnesses, and unique-solution replays.

For 5x5, the ONLY currently enumerated domain contains states reachable
with occupancy <=4. Occupancy never decreases: removing a blank introduces
one mark, removing your own marked cube preserves mark count. Consequently
a path to a state with <=K marked cells cannot leave and re-enter the
occupancy-bounded domain. The implementation is limited to K<=4 pending a separate memory-aware analysis for higher K. The reference BFS explores all same-occupancy
cycles; the independent checker tests all legal outgoing bitboard actions
and the exact restricted closure. Its classes are *positions*, NOT
unrestricted 5x5 forced-win puzzles.

A trivial safe upper bound for any one fixed objective family on 5x5
is the number of **all** D4 board-and-turn orbits, even illegal pairs:
2 * (3^25 + 4*3^15 + 3^13 + 2*3^7)/8 = 211,836,900,942.
This is an upper bound, neither an estimate nor a verified reachable count.

## Reproduction

- python -m quixoforge.census --size 3
- python -m quixoforge.census --size 3 --verify
- python -m quixoforge.census --size 3 --family P2_unique_win
- python -m quixoforge.census --size 5 --max-stones 4 --verify
- python -m pytest -q tests/test_census.py

Family exports are JSONL objects containing canonical board, side to move,
objective, winning actions and a shortest X-first legal move history.
No arbitrary 5x5 setups or speculative global counts are exported.
Proof assistant certification and psychological validation are not claimed.
