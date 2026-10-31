# Certified 5×5 Quixo puzzle generation and game-count contracts

The 5×5 QuixoForge application has two independent goals:
1. Generate **playable, reproducible, proven** tactical puzzles.
2. Report the count of playable games without conflating move histories,
   board/turn positions, geometrically distinct puzzles, and human meaning.

## Generator contract

Input: integer seed, desired number of distinct puzzles, forced-win depth
(in legal *plies*), optional unique-first-move flag, and fixed budgets.

For each generated puzzle:
- Construct the board solely through an **X-first legal move history**
  from the empty official 5×5 starting board. Stop the history before
  the first terminal winner.
- Use two independent finite-horizon solvers to prove that the player to
  move can force victory within the stated number of plies.
- Record and independently verify an AND/OR certificate that covers
  **every legal opponent reply**.
- Audit the complete winning first-move set; require exactly one when
  `unique=true`.
- By default require the stated depth to equal the **minimum** proven
  forced-winning horizon, so a win-in-one cannot masquerade as a
  nontrivial three-ply puzzle.
- Deduplicate by square **D4 rotation/reflection** of the board,
  retaining player colors and side to move.
- Export each puzzle with the board, player to move, complete legal
  history, solution moves, minimal forcing horizon, orbit identifier,
  and proof certificate.
- On failure to meet the requested quota within the declared search
  budget, **raise an error; never publish a partial bank as complete**.

### Commands

Install the project (`pip install -e .`) and run:

```sh
# Print the exact infinite-history result and rigorous finite bounds
quixoforge count-5x5

# Generate one or more mathematically certified win-in-one puzzles
quixoforge generate-bank --count 2 --seed 42 --depth 1 \
  --searches 500 --attempts-per-search 200 --output puzzles.json

# Independently replay and verify EVERY puzzle in the saved bank
quixoforge verify-bank --input puzzles.json

# Generate proper multi-step puzzles: attacker, defender, attacker
quixoforge generate-bank --count 1 --seed 2026 --depth 3 \
  --searches 1000 --attempts-per-search 150 --output win3.json

# Allow multiple winning first actions, without relaxing the proof
quixoforge generate-bank --count 3 --seed 9 --depth 1 \
  --allow-multiple --output tactics.json
```

The generator uses a deterministic seeded sampling policy, not an
assumption that random positions are solvable. A single generated sample
is **not** a proof of catalogue completeness. It is legal and solvable
because its actual certificate passed the verifier.

A `depth=3` puzzle means **three total plies** (attacker moves,
defender replies, attacker wins); it does not mean three full turns
by the attacker. Ordinary Quixo rules and the end-of-game condition
are enforced on every branch.

## Four different "numbers of games"

| Object | Mathematically exact or current research evidence |
| --- | --- |
| Ordered legal first-win move histories with repetitions permitted | Exactly **countably infinite** (proved constructive repeatable two-move cycle) |
| All legally reachable 5×5 board-and-turn states | **Unknown finite global count** |
| All reachable nonterminal positions up to board symmetry | **Unknown global count**, rigorous upper bound 192,103,543,264 |
| Currently certified finite-domain tactical puzzle classes | **At least 5,435,153**: 5,434,783 win-in-one through nine marked cubes plus 370 additional three-ply forced wins through seven marked cubes |
| Classes with exactly one certified winning first action among those families | **At least 1,942,980** |
| Reachable nonterminal forcing-win puzzle D4 classes globally | **Unknown exact number**, rigorous upper bound **100,535,249,578** from published strong-solving results and independent combinatorics |
| Subjectively meaningful human logic puzzles | Not a number until a specific meaning/difficulty criterion is defined |

The raw 2,530,588,373 number is the **complete occupancy≤9 reachability
census**, including finished positions. It is **not** a full-game count,
a count of complete games, or a number of already-exported puzzle files.

Existing Quixo 5×5 solving and tiering research is credited in
[our census notes](CENSUS_5X5_R7_V14.md) and
[global cardinality theorem notes](GLOBAL_5X5_CARDINALITY_THEOREMS.md).

## Beyond the bounded catalogue

To obtain the exact finite total of playable board-position puzzles,
the project must (1) define the objective/human meaningfulness criterion,
(2) traverse *all* 0..25 occupied-cube reachable strata with terminal
stopping and correct same-stratum cycle closure, (3) classify the chosen
winning/tactical property for **every** root, and (4) independently
validate the counts. The row/occupancy decomposition in
[TWO_COLOR_LAYER_SATURATION_THEOREM.md](TWO_COLOR_LAYER_SATURATION_THEOREM.md)
is a valid route, but these full-domain computations have not been
performed. No finite exact count may be inferred from the proved
infinite move-history result.
