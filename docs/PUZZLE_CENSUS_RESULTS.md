# QuixoForge — exact puzzle-census results (research phase 1)

All counts refer to terminal-stopped, X-first, two-player games with exact
unrestricted graph-value semantics. These are measured finite-domain results,
not a published novelty claim, human difficulty rating, or global 5x5 count.

## Complete 3x3 reachable universe

| Family | Raw states | D4 orbits |
|---|---:|---:|
| Reachable, all | 32,027 | 4,433 |
| Terminal (excluded from puzzles) | 11,770 | 1,644 |
| P0 nonterminal | 20,257 | 2,789 |
| P1 eventual forced win | 15,167 | 2,062 |
| P2 exactly one winning action | 1,648 | **212** |
| P4 P2 + at least 3 plies + branching reply | 384 | **48** |
| Exactly one fastest winning action | 2,768 | 362 |
| Multiple winning actions | 13,519 | 1,850 |
| Forced loss | 5,090 | 727 |
| Exactly one maximum-delay action | 432 | 56 |

All directed legal action edges: 276,936. Outcomes including terminals:
WIN 20,247, LOSS 11,780, NONFORCED 0. The empty start has WIN remoteness
seven plies. P1 raw states partition as P2 (1,648) and multiple-win
(13,519). P0 nonterminal partitions into P1 WIN (15,167) and forced-loss
(5,090). All reachable partitions into 20,257 nonterminal plus 11,770
terminal.

All-state D4 orbit Burnside fixed-incidence sum: 35,464 = 8 * 4,433.
Nonterminal orbit-size histogram (size -> classes):
1 -> 3, 2 -> 13, 4 -> 489, 8 -> 2,284.
P2 orbit sizes: 4 -> 12, 8 -> 200. P4: 8 -> 48.

### Exact remoteness classification of WIN orbit representatives

| Plies | P1 forced-win orbits | P2 unique-action orbits |
|---:|---:|---:|
| 1 | 1,806 | 164 |
| 3 | 178 | 34 |
| 5 | 71 | 10 |
| 7 | 7 | 4 |
| Total | 2,062 | 212 |

The remoteness distribution is not a human difficulty study. The nontrivial
P4 family intentionally excludes one-ply recognition and single-response
lines; it does not prove that humans find every P4 position difficult.

## Exact restricted 5x5 reachable domain: occupancy <=4

| Occupancy | Reachable states | D4 classes |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 16 | 3 |
| 2 | 468 | 60 |
| 3 | 11,812 | 1,512 |
| 4 | **187,164** | **23,659** |
| Total | **199,461** | **25,235** |

Both independent tuple-array and bitboard complete BFS enumerators matched
199,461 states, 7,945,716 legal candidate actions, and 1,253,304 actions
remaining within occupancy <=4. The independent bitboard orbit enumeration
had Burnside incidence sum 201,880 = 8 * 25,235, distributed by orbit
size: size 1 -> 1, size 2 -> 4, size 4 -> 597, size 8 -> 24,633.
All positions in occupancy <=4 are nonterminal because fewer than five
marked cubes cannot form a line of five. These are structural positions,
NOT proven full 5x5 tactical puzzles. No counts above occupancy 4 are
claimed. One bitboard local Python 3.13.5 run took 2.70 seconds for
BFS and 13.23 seconds including D4 stabilizer measurement, whereas
a separate tuple-reference BFS took approximately 6.01 seconds.
These are **non-equivalent workloads**, not a performance comparison.

## Reproduction / independent evidence

The initial separate Python 3.13.5 standalone oracle implemented full
tuple-based BFS, exact retrograde propagation, canonical orbit partition,
and an independent Burnside fixed-state identity. Its canonical JSON
summary (excluding timing) has SHA256:

5dbb055fa55a73ce67f8c2aced72560220a732fdeb887c29597bf2b7e3c7ac06

The repository production census independently reads the pinned full
3x3 tablebase, classifies all actions with the reference list-shift
rules, and groups by canonical D4 key. The separate verifier executes
another complete bitboard graph retrograde solution, checks each
tablebase entry, independently rebuilds every family predicate using
the bitboard engine, and counts orbits with stabilizer weights instead
of shared canonical-key grouping. The 5x5 restricted-domain verifier
uses bitboard legal actions and independent rotation maps.

Executable gates:

- python -m pytest -q tests/test_census.py
- python -m quixoforge.census --size 3 --verify
- python -m quixoforge.census --size 5 --max-stones 4 --verify
- python -m quixoforge.census --size 3 --family P2_unique_win

Record GitHub Actions branch run and commit when interpreting this
document. Tests must pass at the committed SHA before promoting the
repository verification to a completed CI claim.

## Mathematical / epistemic ledger

PROVED: D4 equivariance of the pinned geometric move semantics and
orbit-stabilizer/Burnside identity; occupancy monotonicity and exactness
of occupancy-restricted BFS with all same-occupancy transitions.

COMPUTATIONALLY EXHAUSTIVE: specified 3x3 states and exact predicate
counts, and 5x5 occupancy<=4 reachable structural counts, provided
the independent graph/checksum/CI gates pass at the pinned revision.

NOT PROVED: a complete reachable-state or puzzle total for 5x5,
human-rated intellectual difficulty, equivalence stronger than D4,
novelty of the specific counts relative to all literature, and formal
verification of Python source with a proof assistant.
