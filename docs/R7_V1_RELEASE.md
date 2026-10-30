# R7 v1.0 — scoped complete-engine research release

**Contract:** deliver a headless playable two-/four-player engine with independently verifiable transitions, exact finite-horizon solvers, proof-checked tactical puzzles, reproducible generator and benchmark, and a tested bounded competitive opponent. A complete mathematical solution to every Quixo position is **not** an engineering requirement that can be claimed without exhaustive game-graph solution/proof.

## Completed implementation contracts

| Gate | Implementation | Independent evidence | Status |
|---|---|---|---|
| Official 2-player legal moves and terminal precedence | `reference`, `bitboard` | Full opening two-ply transition comparison, randomized replay and negative cases | VERIFIED for executed coverage |
| Official 4-player point and team rules | `teams`, `team_bitboard` | Full opening 88 pointed actions and independently checked random legal games; pass and first-round tests | VERIFIED for executed coverage |
| Both variant solvers | `solver.ReferenceSolver` with four-player adapters; bitboard two-player solver | Independent 4-player adapter equality over seeded states, deterministic finite horizon | VERIFIED for tested horizons |
| D4-safe transpositions and opponent | `engine.AlphaBetaEngine` | Independent exhaustive minimax at depth 1/2 and independent depth-3 sampled positions; eight symmetries | VERIFIED for tested horizons |
| Interrupted search rollback | `engine.recommend` | deterministic low-node cutoff returns last completed result, never a partial score | VERIFIED |
| Reproducible tactical certificates | `generator`, `generic_proof`, `team_puzzles`, `verify_examples`, `puzzles` | two-player and four-player fixtures proof-checked against independent transition models; corrupt metadata/proofs rejected | VERIFIED |
| Reachability with <=3 marks | `reachability` | all 12,297 reachable states and all 498,328 legal candidate edges cross-checked by independent bitboard BFS | VERIFIED in finite domain |
| CLI, package and unit tests | `cli`, `pyproject.toml`, `.github/workflows/ci.yml` | local pytest, wheel building where available, remote matrix CI | Requires commit-specific CI result |
| Benchmark fairness | `engine_bench`, `bench` | baseline and alpha-beta scores asserted equal before timing results emitted | VERIFIED for sampled workloads |
| SOTA superiority over external engines | N/A | No like-for-like tournament or external baseline | UNVERIFIED, not claimed |
| Globally solved game/repetition | N/A | Exhaustive full graph and infinite-play rule unresolved | UNVERIFIED, not claimed |

## Critical semantics

1. X/O marks are team ownership, not physical seat identity. In four-player mode the marked cube pointer may face either member of its own team; on selecting it only the pointed-to seat may extract it, unless in the blank-only first round.
2. After a move to a double-line board, the **mover loses** in both variants.
3. Four-player compulsory passes are present only when no cube is legally selectable. An arbitrary shaped board may still be historically unreachable; `replay` is the constructive witness.
4. Bounded `WIN` and `LOSS` are proof values; `UNKNOWN` does not mean draw. Heuristic alpha-beta score is not a proof value.
5. During full finite-depth minimax the transposition table is indexed by D4 canonical tuple and explicit depth; PV moves are transformed back to original board orientation.
6. Exact sparse-state BFS prunes moves selecting blanks *when at maximum occupation*, preserving the complete induced graph because occupancy cannot decrease. The metric `examined_edges` counts candidate legal actions even when pruned prior to materializing a child.

## Evidence records (local)

- Python: 3.13.5. `PYTHONPATH=src python -m pytest -q`: 46 passed (including four-player proof fixture verification) after transition-validation optimization; execution environment Linux x86-64.
- `PYTHONPATH=src python -m quixoforge.verify_examples`: 3 replay-checked two-player JSON fixtures plus 1 replay-checked four-player fixture (`python -m quixoforge.team_puzzles`).
- `PYTHONPATH=src python -m quixoforge.engine_bench --seed 917 --count 6 --plies 14 --depth 2 --repeats 2`: matched independent exact evaluation on all inputs; median alpha-beta **172 nodes / 10,603,164.5 ns**, median independent brute **911 nodes / 64,061,719 ns**. These are exploratory local measurements and cannot establish worldwide SOTA strength or performance. The fixed-depth heuristic objective and timings are in `benchmarks/engine_v1_0_local.json`.
- Five adversarial dimensions: corrupted proof, false puzzle horizon metadata, malformed 4-mask state, illegal pass, and unfinished iterative search. Historical evidence in `docs/EVIDENCE.md`.

## Assumptions and unproved claims

- No game-theoretic full solution or repeat adjudication: **UNVERIFIED**. Quixo can cycle; a bounded strategy cannot guarantee a decision for arbitrary play.
- Full arbitrary-board reachability beyond three marked cubes: **UNVERIFIED**; `OUT_OF_SCOPE` deliberately distinct from `UNREACHABLE`.
- Human skill difficulty and external engine Elo: **UNVERIFIED**; tactical depth alone is a mathematical classification, not psychometric measurement.
- Exact formal source-code verification by Lean/Coq: **UNVERIFIED**; finite/exhaustive-slice evidence does not imply a mechanized proof of Python itself.
- Social 4-player rules (clockwise physical turn assignment, permission to confer, physical orientation) modelled as seat order and mark orientation. Social consultation is not represented in board transition logic.
- CI on this revision is **UNVERIFIED until remote GitHub Actions passes**. Never backfill a CI pass based on a local suite.

## Prior-art / novelty boundary

Fixed-depth minimax with alpha-beta has existing Quixo implementations (e.g. https://github.com/poyrazn/quixo). This project does **not** claim inventing alpha-beta or solving the Quixo opening. The research contribution is reproducible, independent reference/optimized verification plus strict evidence provenance and finite-domain certificates.

## Historical correction appended in v1.1 (2026-10-30)

This v1.0 document's wording that 5x5 Quixo has no published full-game solution was **incorrect**. The 5x5 opening was already solved as a draw by Tanaka et al. (2020) and reproduced by Shi (2024). This v1.1 release includes our independently reproduced *3x3* exact game-graph solution and tablebase; see `R7_V1_1_TABLEBASE.md`. The local codebase has not reproduced the massive 5x5 analysis.
