# UCS-Pro R7 requirement, assumption and evidence ledger

## Contract

| ID | Requirement | Source | Acceptance target | Current evidence / status |
|---|---|---|---|---|
| R01 | Exact official 2-player moves and terminal outcomes | user/domain | agree with rule text + independent path | Tests and rule citation; local VERIFIED |
| R02 | Strict state validation | user | immutable shape, rejects illegal replay | Unit tests; local VERIFIED for witnessed states; arbitrary-state reachability UNVERIFIED |
| R03 | D4 symmetry reduction | user | transforms commute with moves; orbit-invariant caches | Eight automorphisms and differential tests; local VERIFIED for tested cases |
| R04 | Independent reference and optimized algorithms | user | separate transitions and winner checks | modules + exhaustive depth-2 opening + seeded tests; local VERIFIED for tested cases |
| R05 | Provably bounded tactical puzzles | user | complete independent finite AND/OR verifier | committed JSON proof trees; replay and checker; local VERIFIED at depths 1 and 3 |
| R06 | Difficulty classification | user | deterministic declared definition | minimal proven tactical horizon; local VERIFIED, human difficulty NOT claimed |
| R07 | Reproducible benchmarking | user | fixed seeds, parameters, environment, equality | benchmark script and evidence; local VERIFIED for execution; speed superiority UNVERIFIED |
| R08 | Automated tests | user | executable local suite and configured CI | local VERIFIED; CI status requires GitHub run |
| R09 | Extensibility | user | game protocol apart from Quixo internals | `FiniteGame` and toy-game test; local VERIFIED for minimal interface |
| R10 | Exhaustive verification where feasible | user | scope-bounded exhaustive edge cases | complete opening two-ply tree; local VERIFIED for that scope, full tree UNVERIFIED |
| R11 | Official 4-player team variant | implied by 'exact game rules' | oriented cubes and teammate turn semantics | NOT IMPLEMENTED; PARTIAL scope, clearly excluded |
| R12 | Defer UI and infrastructure | user | headless package only, minimal CI | local VERIFIED |

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
- Full arbitrary-position reachability: **unproved and not computed**.

## Verification and failure log

- Initial tests had two incorrect test expectations (bogus always-failing conditional test and toy-game outcome inversion). Repaired tests, no production rule changes; rerun suite passed.
- Hard performance superiority gate is NOT closed: first measured depths showed similar runtime. No benchmark manipulation or doctored numbers.
- PDF source independent visual screenshot attempt failed due provider cache miss; original rulebook textual extraction was accessible.

## Next evidence gates

1. CI verify on committed head and compare local commands with workflow.
2. Increase tactical corpus with diverse nonterminal histories; check independent transition equivalence and certificate mutation tests at greater depths.
3. Compare performance on symmetric openings and midgame workloads with pinned benchmark JSON, confidence intervals where appropriate.
4. Formalize a rule model independently in a proof assistant if seeking unconditional machine-checked rule-equivalence claims.
