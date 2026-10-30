# UCS-Pro R7 requirement, assumption and evidence ledger

## Contract

| ID | Requirement | Source | Acceptance target | Current evidence / status |
|---|---|---|---|---|
| R01 | Exact official 2-player moves and terminal outcomes | user/domain | agree with rule text + independent path | Tests and rule citation; local VERIFIED |
| R02 | Strict state validation | user | immutable shape, rejects illegal replay | Unit tests + exhaustive occupancy<=3 BFS; VERIFIED within finite domain; unrestricted arbitrary-state reachability UNVERIFIED |
| R03 | D4 symmetry reduction | user | transforms commute with moves; orbit-invariant caches | Eight automorphisms and differential tests; local VERIFIED for tested cases |
| R04 | Independent reference and optimized algorithms | user | separate transitions and winner checks | modules + exhaustive depth-2 opening + seeded tests; local VERIFIED for tested cases |
| R05 | Provably bounded tactical puzzles | user | complete independent finite AND/OR verifier | committed JSON proof trees; replay and checker; local VERIFIED at depths 1 and 3 |
| R06 | Difficulty classification | user | deterministic declared definition | minimal proven tactical horizon; local VERIFIED, human difficulty NOT claimed |
| R07 | Reproducible benchmarking | user | fixed seeds, parameters, environment, equality | benchmark script and evidence; local VERIFIED for execution; speed superiority UNVERIFIED |
| R08 | Automated tests | user | executable local suite and configured CI | local VERIFIED; CI status requires GitHub run |
| R09 | Extensibility | user | game protocol apart from Quixo internals | `FiniteGame` and toy-game test; local VERIFIED for minimal interface |
| R10 | Exhaustive verification where feasible | user | scope-bounded exhaustive edge cases | complete opening two-ply tree + 12,297-state occupancy<=3 graph, independently re-enumerated; VERIFIED for finite scope, full tree UNVERIFIED |
| R11 | Official 4-player team variant | implied by 'exact game rules' | oriented cubes and teammate turn semantics | NOT IMPLEMENTED; PARTIAL scope, clearly excluded |
| R12 | Defer UI and infrastructure | user | headless package only, minimal CI | local VERIFIED |
| R13 | Exact unrestricted-depth sparse-state reachability | domain follow-up | for <=3 marks decide yes/no with shortest witness, independently enumerate closure | reference BFS/bitboard BFS set equality, 498,328 tested edges, D4 covariance, shortest-distance checks; local VERIFIED (domain only) |

`VERIFIED` here means observed on the stated revision and finite test coverage, **not** a global correctness theorem. See run logs in GitHub Actions for CI revision-specific evidence.

## Assumptions and applicability

- A01 (medium): Two-player match is the core research target; four-player variant remains separate and unimplemented, not a silent simplification.
- A02 (high): Players announce a winning line promptly; the engine resolves the position immediately, not human announcement/retraction disputes.
- A03 (high): Infinite repetition has no automatic draw. Bounded solver returns `UNKNOWN`, never substitutes an invented draw convention.
- A04 (medium): Proof certificates target bounded tactical outcomes rather than general Quixo game-theoretic solution.
- A05 (low): Python >= 3.10 and pytest are sufficient. No database, service, authentication, telemetry or deployment platform is applicable to this local core.

## Claims ledger

- Opening legal-move count 44: exact combinatorial argument + executable enumeration.
- Reference/bitboard transition agreement: **observed for tested positions**, not for every one of the `3^25` boards.
- Forced wins in examples: **inductively checked finite proof trees** using the declared rule semantics.
- Bitboard is faster: **not asserted**. Symmetry reduces visited nodes in symmetric regimes, but overhead may negate any runtime advantage.
- Opening game-theoretic win/loss/draw: **unproved and not computed**.
- Sparse-state reachability for occupancy <=3: **exhaustively enumerated** and matched by an independent bitboard graph BFS (12,297 states, 498,328 examined transitions for fixed starter), with independent shortest-path checks; mathematically complete within its occupancy domain by monotonicity. Not a proof of implementation-level correctness without trusting both transition models.
- Full arbitrary-position reachability: **unproved and not computed** for occupancy >=4.

## Verification and failure log

- Initial tests had two incorrect test expectations (bogus always-failing conditional test and toy-game outcome inversion). Repaired tests, no production rule changes; rerun suite passed.
- Hard performance superiority gate is NOT closed: first measured depths showed similar runtime. No benchmark manipulation or doctored numbers.
- PDF source independent visual screenshot attempt failed due provider cache miss; original rulebook textual extraction was accessible.

## Next evidence gates

1. CI verify on committed head and compare local commands with workflow.
2. Expand exhaustive reachability beyond 3 marks using proven-pruning and memory budgets, then increase tactical corpus with diverse nonterminal histories.
3. Compare performance on symmetric openings and midgame workloads with pinned benchmark JSON, confidence intervals where appropriate.
4. Formalize a rule model independently in a proof assistant if seeking unconditional machine-checked rule-equivalence claims.

## R7 v0.2 follow-up evidence (local)

- **CONTRACT**: R02/R10 expanded and R13 introduced for exact reachability within occupancy 0..3; no claim of full-board reachability.
- **SPEC**: `ReachabilityIndex` performs unrestricted-depth BFS on all reachable positions with occupancy<=K, fixed starting symbol, rejects out-of-domain queries and supplies replay-checkable shortest paths.
- **VERIFY**: independent optimized BFS enumerates all 12,297 reachable states and agrees with reference BFS on all states and all 498,328 examined transitions (X starter, cap 3); D4 covariance tested on every reachable state; 1,576 geometric orbits observed. The two separate BFS shortest-distance maps agree on all reachable cap-3 positions. Structural states with impossible mark histories reject as expected.
- **FALSIFY**: blank board with opposite turn, marks confined to an impossible center-only first move, all-X 3-cube position, out-of-domain target, invalid cap/start and malformed CLI inputs explicitly tested. `OUT_OF_SCOPE` never becomes `UNREACHABLE`.
- **LIMITS**: Python source code has not been formally verified in Lean/Coq; reference and optimized implementations remain software oracles, not axioms. Test scope is exact for occupancy<=3 only. CI status must be checked on the new commit before this revision can be marked remotely VERIFIED.
