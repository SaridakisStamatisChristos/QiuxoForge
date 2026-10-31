# QuixoForge

[![Python tests](https://github.com/SaridakisStamatisChristos/QiuxoForge/actions/workflows/ci.yml/badge.svg)](https://github.com/SaridakisStamatisChristos/QiuxoForge/actions/workflows/ci.yml)

**Research-grade, headless Quixo engine — complete playable rules for two and four players, independent rule implementations, exact bounded proof engines, practical alpha-beta opponent, reproducible puzzle generator, exhaustive sparse-state verification.** No UI, server, external assets or runtime third-party dependencies. The GitHub repository is intentionally named `QiuxoForge`; the package import is `quixoforge`.

## Supported capabilities

| Area | Delivered / independent verification |
|---|---|
| Two-player rules | Exact selection, shift, ownership, no return to source, terminal precedence; list-shift and separately implemented 25-bit masks |
| Four-player rules | Four clockwise seats in opposing teams, pointed-cube ownership, either teammate pointer orientation on insertion, four-turn blank-only first round, compulsory pass only when no selectable cube; independently implemented reference and four-mask bitboard rules |
| State validation | Strict immutable domain validation; legal-history replays; exact *unrestricted-depth* reachability with shortest witnesses for boards holding 0–3 marks, no false verdict outside domain |
| Symmetry | All eight board D4 rotations/reflections for two-player geometry; canonical bitboard transpositions and move-coordinate restoration in alpha-beta; no unjustified four-player reflection reduction |
| Bounded solvers | Two-player reference/bitboard and four-player reference/bitboard **exact finite-horizon** `WIN/LOSS/UNKNOWN` proofs (not an unbounded solution) |
| Tactical proof | Fully expanded AND/OR certificates for two-player forcing wins, independently replay-checked including every defender branch; unique winning moves and exact minimal forcing depth |
| Playable opponent | Iterative-deepening alpha-beta, deterministic heuristic, D4 transposition bounds, tactical move ordering, best complete-iteration result on node budget; scores are *heuristic*, not certificates |
| Puzzle generation | Seeded legal playouts, D4 deduplication, independent exact audit, proof verification, reproducible JSON fixtures; explicit error rather than uncertified result |
| Research evidence | Differential tests, independent brute-force fixed-depth minimax oracle, complete 3-mark state graph, official source checks, JSON benchmarks, unit tests and CI |
| **Exact 3x3 solved variant** | Exhaustive loopy retrograde analysis, full **32,027-state** and **276,936-transition** graph; separate list and bitmask implementations agree on *every* state/outcome/remoteness/edge; SHA256-verified 83 KB optimal-move tablebase |

### Installation and tests

Requires Python 3.10+. No dependencies for runtime. `pytest` is optional for tests.

```sh
python -m pip install -e '.[test]'
python -m pytest -q
python -m quixoforge.verify_examples
python -m quixoforge.tablebase
python -m quixoforge.tablebase --rebuild  # checks all 32027 states with independent oracles
python -m quixoforge.team_puzzles
python -m quixoforge.bench --seed 711 --count 3 --plies 6 --depth 1 --repeats 1
python -m quixoforge.engine_bench --seed 917 --count 6 --plies 14 --depth 2 --repeats 2
sha256sum -c SHA256SUMS
```

### CLI (no UI)

```sh
quixoforge show 0:R 5:D
quixoforge micro  # full exact 3x3 solution, X wins in seven plies
quixoforge micro --board ......... --turn X
quixoforge solve --depth 3 0:R 5:D
quixoforge opponent --depth 4 --max-nodes 100000 0:R 5:D
quixoforge team --depth 1 0:R:2  # seat 0 plays X, directs cube point to teammate seat 2
quixoforge team-certify --depth 1 <replayed team actions>  # complete four-player AND/OR proof
quixoforge generate --seed 7197 --depth 1 --attempts 50 --min-plies 15 --max-plies 36
quixoforge reach --board 'X........................' --turn O --start X --max-stones 3
```

For `team`, seats `0/1/2/3` are north/east/south/west in clockwise order, with teams `(0,2)` = X and `(1,3)` = O. The source position is indexed row-major `0..24`. For two-player moves, `index:edge` (`L/R/U/D`) names the insertion end, not a displacement direction. For team moves `index:edge:point` also names which seat the cube's point faces. `PASS` is legal *only* when no marked cube pointing to that player or blank cube is available (never after a winning line). Four-player rows and columns are shared physical cubes; teammates do not each own their own colored marking.

`opponent` returns the strongest **completed** search iteration, node count, score and principal variation (until only exact transposition entries remain). If the budget prevents completing even depth 1, it returns no move rather than an unverified action. `solve` emits three-valued, independently agreed *finite-horizon* outcomes; a heuristic recommendation is **never** mislabeled as a game-theoretic win.

`generate` produces a self-contained JSON schema-1 certificate, with source replay history, complete solution list and a checked proof tree. A difficulty label means minimal winning depth among the tested bounded horizons, not human cognitive difficulty. Four-player puzzles use `quixoforge team-certify`, and are checked using `python -m quixoforge.team_puzzles`; the optimized four-mask solver creates a proof checked independently against the reference team model. To validate a generated JSON file, save it to `puzzle.json` and run `python -m quixoforge.verify_examples puzzle.json`.

### Exact reachability boundary

Positions containing at most **three marked cubes** can be answered `REACHABLE` (with a shortest legal history) or `UNREACHABLE` by an exhaustive *unrestricted-ply* graph search. The occupancy bound is not a ply bound, and monotonicity of occupied-cube count proves completeness of this finite slice. Requests containing four or more marks produce `OUT_OF_SCOPE` — never a false negative. There are 12,297 reachable `(board, turn)` states for X starting and a three-mark bound, independently re-enumerated via bitboards. Full arbitrary-board reachability and solving the entire potentially cyclic Quixo game are **not asserted**.

## Correctness scope and limitations

- All rules follow the [Gigamic English rulebook](https://cdn.1j1ju.com/medias/a8/5e/26-quixo-rulebook.pdf) (two-player and four-player sections, p. 4). Human declarations, consultation between teammates and tournament clocks are social rules, not game-state transitions.
- Bounded proof certificates are inductively valid under the source model; Python code has *not* been proved by a theorem assistant. Finite tests cannot prove all possible 25-cell board configurations.
- No official indefinite repetition/draw rule has been invented. `UNKNOWN` means no outcome was certified inside the requested horizon. The 5x5 initial position has already been solved as a theoretical draw (Tanaka et al. 2020, replicated by Shi 2024). **QuixoForge does not reproduce that 5x5 solution**. The 3x3 game variant is now fully solved and independently cross-checked in QuixoForge; `NONFORCED` denotes lack of a forced terminal win, not an invented official repetition adjudication.
- Four-player geometric reflections do **not** automatically preserve clockwise seating; its solver therefore uses exact non-symmetry reference/bitboard caches rather than unsound reductions.
- Local alpha-beta performance numbers are for the declared positions/depth/runtime; there is no general SOTA or outperform-all-engines claim. Competitor comparisons require equivalent rules/inputs/hardware.

### Established prior art and correction

The normal **5x5 Quixo is already solved** as a game-theoretic draw (Tanaka, Bonnet, Tixeuil and Tamura, [*Quixo Is Solved* (2020)](https://arxiv.org/abs/2007.15895)). [Robert Shi's 2024 Berkeley report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-139.pdf) independently reproduced that outcome and counted **32,027** reachable 3x3 positions, with a first-player win in **7** moves. QuixoForge v1.1 independently reproduces **the full 3x3 graph**, not the massive 5x5 computation. We do not claim novelty for these previously established results.

Read the [v1.1 full tablebase evidence](docs/R7_V1_1_TABLEBASE.md), [formal model](docs/RESEARCH.md) and [evidence ledger](docs/EVIDENCE.md). See [v1 contract and measured verification](docs/R7_V1_RELEASE.md). The game is designed by Thierry Chapeau and published by Gigamic; independent code contains no artwork or copied rulebook.

MIT licensed.


## Exact Quixo Puzzle Census (v1.2 research)

The primary objective is counting mathematically distinct, **meaningful and
independently certifiable puzzles**, not solving the already-solved 5x5
opening again. The full X-first 3x3 reachable graph has 32,027 states,
4,433 D4 orbits, 2,789 nonterminal orbits, 2,062 winning-position orbits,
**212 unique-winning-first-action puzzle orbits**, and **48 uniquely
winning, remoteness-at-least-3, branching-opponent puzzle orbits**.
These counts are exact for their explicitly defined families; they are not
estimates of all possible human puzzles.

The exact X-first 5x5 occupancy<=4 reachable slice contains
**199,461** position states and **25,235** D4 orbits. These are position
counts, not a full 5x5 tactical census.

Run:
- python -m quixoforge.census --size 3 --verify
- quixoforge census --size 3 --family P2_unique_win
- python -m quixoforge.census --size 5 --max-stones 4 --verify

See docs/PUZZLE_CENSUS_SPEC.md for semantic definitions and equivalence
proofs, and docs/PUZZLE_CENSUS_RESULTS.md for complete distributions,
reproduction and limitations. The puzzle record stream includes complete
winning first-action sets and shortest legal setup histories. Family labels
measure mathematical forced-win structure, not human-rated difficulty.

An additional exact contingent-response family has **40 D4 puzzle classes**:
two possible opposing replies require disjoint sets of next winning moves.
This is a stricter mathematical criterion than the 48-class P4 family.

## Full-board 5x5 tactical census (v1.3)

QuixoForge now enumerates all reachable **5x5** two-player X-first positions with up to five marked cubes using a D4 orbit-quotient BFS. It finds **2,254,843** reachable board/turn states in **283,316** geometric orbits and independently checks all positive first-move win certificates: **120** geometrically distinct win-in-one problems, of which **46** admit exactly one winning first action. Every exported puzzle includes a replayable shortest X-first history. A completely separate unsymmetrized tuple-array BFS has also reconstructed all 2,254,843 raw reachable states and verified all five occupancy layers. These are precisely scoped one-ply tactical results, **not** the global number of meaningful 5x5 puzzles.

```sh
quixoforge census5 --max-stones 5 --verify
quixoforge census5 --max-stones 5 --family unique_win_in_one
```

See [the 5x5 tactical census](docs/CENSUS_5X5_TACTICS.md) for definitions, methods, evidence, and remaining validation gates.

## Large-scale 5x5 puzzle census (native R7 v1.4)

The native full-board 5×5 D4-quotient enumerator has now completely traversed **603,033,221 legally reachable board/turn states with ≤8 marks** in **75,434,676 geometric classes**, including **698,588 win-in-one puzzle classes** and **243,957 classes with exactly one immediately winning legal action**. Those counts are finite-domain computations, **not** a global count of all meaningful puzzles. An independently coded, unsymmetrized C++ tuple-array BFS confirms all **18,608,279 states with ≤6 marks**, including the 552 terminal states in occupancy six. An independent raw tuple-array BFS has fully reconstructed **all 118,302,019 states through seven cubes** and independently checked the 510,500 / 171,788 winning/unique raw-action totals. The eight-cube figures have also been independently reproduced by a second raw tuple-array BFS over **603,033,221** distinct states, checking all immediate-winning actions, including negative cases and cap-crossing winning moves.

**One-command full verification** (C++17, Python 3.10+ and POSIX shell):

~~~sh
sh tools/run_full_5x5_r7.sh
~~~

Or run the tools separately:

~~~sh
c++ -O3 -std=c++17 tools/census5_native.cpp -o /tmp/qf-census5
c++ -O3 -std=c++17 tools/verify5_native_raw.cpp -o /tmp/qf-raw5
/tmp/qf-census5 8 100000000
/tmp/qf-raw5 6
python -m quixoforge.census5_forced3 --verify
~~~

See [formal results, claims and reproduction gates](docs/CENSUS_5X5_R7_V14.md). The previous Python `census5` command remains valid for the original five-cube witness-export domain; the native executable is for large-scale reproducible counting.

An independent attacker/defender/attacker census over all ≤7-mark roots has also certified **370 new forced-win-in-exactly-three puzzle classes**, of which **64** have exactly one forcing first action. All 370 positive complete-branch certificates passed a separate pure tuple-array verifier. Moreover, every one of the 370 is defender-contingent: at least two legal defender replies require disjoint sets of winning final moves. The all-negative census relies on the exhaustive native search.

Existing Quixo tiering and strong-solving research predates this project (Tanaka et al., *Quixo Is Solved*, 2020; Robert Shi, Berkeley UCB/EECS-2024-139, 2024, Chapter 7.2). The novelty claim is limited to our particular *reachable tactical puzzle census and independently reproduced counts*; the two-color tier partition is **prior art**, not an invention of QuixoForge.

The exact structural D4 generating function for all 25 occupancy layers is implemented in `tools/structural_orbit_bounds.py`. A proved two-color monotone recurrence that partitions the graph by X/O mark counts is documented at [Two-color layer saturation](docs/TWO_COLOR_LAYER_SATURATION_THEOREM.md). Neither is a claim that the full global puzzle count has been computed.


## Certified 5×5 puzzle-bank generator and full-game count semantics

QuixoForge supports creating **guaranteed playable** X-first 5×5
tactical puzzle banks. Every exported puzzle has a legal move history,
two independent bounded solver checks, a full defender-coverage proof,
and a D4 symmetry identifier. Duplicates are rejected, and any search
that cannot fill the requested bank fails rather than returning an
incomplete catalogue.

```bash
pip install -e '.[test]'
quixoforge count-5x5
quixoforge generate-bank --count 2 --seed 42 --depth 1 --allow-multiple \
    --searches 500 --attempts-per-search 100 --output puzzles.json
quixoforge verify-bank --input puzzles.json
```

**How many games exist?** Complete legal first-win move histories are
**countably infinite** if repeated nonterminal positions are allowed.
The number of distinct *reachable* game positions is **finite but
not globally computed**. The new exhaustive nine-cube dual-color
census has counted **2,530,588,373** raw reachable board-and-turn
states and **316,462,989** geometric classes, identifying
**at least 5,435,153** certified distinct tactical puzzle classes
from the one- and three-ply families; **1,942,980** have exactly
one certified winning first action. These are bounded-domain results,
**not the total number of possible 5×5 puzzles**. The improved
Tanaka-informed global upper bound for reachable forcing-win D4
puzzle classes is **100,535,249,578**, still not an exact total.
See [K9 exact enumeration](docs/EXACT_K9_REACHABLE_CENSUS.md) and
[proof of improved bound](docs/STRONG_SOLVE_PUZZLE_UPPER_BOUND.md).

See [generator and counting contracts](docs/GENERATOR_AND_GAME_COUNT.md)
and [full-game cardinality theorems](docs/GLOBAL_5X5_CARDINALITY_THEOREMS.md).

## Out-of-core census optimization (research)

For larger 5x5 occupancy tiers, the new exact
[external-memory enumerator](tools/census5_dual_tier_external.cpp)
uses a disk-backed FIFO, lazily allocated mmap visited bitmaps,
and immediately reclaims completed tiers. The original in-memory
enumerator remains unchanged as an independent oracle.

```sh
c++ -std=c++17 -O3 tools/census5_dual_tier_external.cpp -o /tmp/quixo-ooc
/tmp/quixo-ooc 8 /tmp > k8-out-of-core.jsonl
python tools/check_dual_tier_census.py k8-out-of-core.jsonl
```

The scratch directory must exist and have adequate **free disk**.
The runner aborts on failed allocations instead of publishing
incomplete census results. This is not yet a restartable all-25-tier
enumerator; see the [architecture and limits](docs/OUT_OF_CORE_CENSUS_ARCHITECTURE.md).

## Exact K11 census and restartable K12 frontier

The out-of-core algorithm has now enumerated **26,651,307,485**
reachable raw 5×5 board/turn states through eleven occupied cubes:
**3,332,049,627** D4 position classes, including
**147,113,673** win-in-one classes and **52,994,624** classes
with exactly one immediate winning first action. With the separate
370 earlier certified non-immediate win-in-three classes, the
lower bound is **147,114,043 distinct tactical puzzle classes**.
The complete K12 starting frontier is archived from successful
GitHub Actions run 41212014946.

The K11 result passed checkpoint consistency validation but has
not been independently re-enumerated by a second K11 algorithm.
The full K0–K25 position and global puzzle counts remain unknown.
See [K11 evidence](docs/EXACT_K11_CHECKPOINTED_CENSUS.md).

To resume the saved K12 frontier and continue into the next
occupancy, the checkpoint loader now supports a *safe upward
occupancy cap extension*, validated against a full independent K7
reference. No completed tiers need to be replayed.
