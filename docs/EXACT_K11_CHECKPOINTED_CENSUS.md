# Exact Quixo 5x5 reachability through K11 — checkpointed census

## Model and exact finite-domain results (31 October 2026)

The out-of-core D4-canonical two-color tier enumerator exhaustively
closed all reachable standard two-player X-first positions through
eleven occupied cubes. The state includes mark colors and the side to
move. Winning terminals are not expanded. All within-tier legal move
cycles were saturated, and every occupancy-increasing transition to
the next layer was recorded in the exact frontier bitmap.

| Quantity | New K11 layer | Cumulative K0..K11 |
|---|---:|---:|
| Raw reachable board/turn states | 17,745,392,476 | 26,651,307,485 |
| Geometric D4 classes | 2,218,496,966 | 3,332,049,627 |
| Terminal raw states | 97,113,048 | 117,842,292 |
| Win-in-one D4 classes | 115,174,547 | 147,113,673 |
| Classes with exactly one winning immediate action | not reported separately | 52,994,624 |

The previously independently verified K<=7 non-immediate win-in-three
family supplies 370 additional distinct classes, of which 64 have
one winning first action. Thus the new known tactical lower bounds
are **147,114,043** distinct first-win puzzles and **52,994,688**
with one winning first action.

These are NOT the global full 25-occupancy position/puzzle counts.

## Execution and evidence

- GitHub Actions success: https://github.com/SaridakisStamatisChristos/QiuxoForge/actions/runs/41212014946
- Source commit: f3b830dc11c317870190b09d921e8a029bc6ab56.
- Results artifact: quixoforge-K11-exact-census-results (ID 13050393214).
- Complete K12 seed/frontier artifact: quixo-K12-resume-frontier (ID 13050497895); archived compressed size ~442.8 MB, multi-GB uncompressed.
- K11 traversal internal elapsed: 5,276.33 s; wall time: 1:28:41; maximum RSS: 5,393,288 KB; exit code: 0.
- Checkpoint consistency verified the entire K10 pinned baseline, legal tier closure and K12 frontier counters. The K12 frontier is a starting set, not a completed K12 census.

**Independent verification status:** K11 was enumerated by ONE D4
two-color exact implementation, with a separate checkpoint consistency
checker and older independent exact censuses through K8. A second,
algorithmically independent K11 graph traversal has NOT been executed.
Do not label K11 as independently replicated.

## Cap extension proof and implication for K12->K13

Every checkpoint is created after a completed occupancy k STRICTLY
below its original cap C. The bitmap frontier for occupancy k+1
therefore contains every legal successor from occupancy k, without
suppression. Occupancy never decreases in Quixo. Hence extending the
requested cap to any C' >= C and resuming from exactly that saved
frontier produces the same reachable states as an uninterrupted run
to C', by induction on occupancy and fixed-point closure within each
(X-count, O-count) tier.

The checkpoint loader now accepts upward cap extensions and rejects
downward changes. A dedicated independent regression verifies a
cap-6-to-cap-7 resume against an uninterrupted K7 reference,
including every exact occupancy and tactical count.

Therefore the archived K12 frontier (original cap 12) can resume
under cap 13 to complete K12 and seed K13, **without replaying
K0..K11**. This is a proven capability, not a claim that K12 has
already completed.

## Citation and evidence discipline

The published Tanaka strong-solving WLD counts give a separate
conditional structural upper bound. They do not determine which
board-and-turn states are reachable from the empty board. The
QuixoForge Python count API explicitly retains null for
the unknown global exact reachable-position and forced-win totals.
