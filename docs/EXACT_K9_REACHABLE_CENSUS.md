# QuixoForge 5x5 complete exact reachability through nine occupied cubes

## Result: new 5x5 X-first reachable root census (terminal-stop)

A newly implemented C++17 D4-canonical reachability enumerator
(tools/census5_dual_tier.cpp) exhaustively explores legal states from
the empty X-to-move root with each color count monotone, including
**all** same-(X-count,O-count) move cycles. It stops immediately at
terminal victories. It counts immediate winning legal actions even
when they temporarily exceed the enumerated root occupancy cap.

An earlier, structurally unrelated implementation in
tools/census5_native.cpp (global canonical hash table), plus a
second unsymmetrized 5x5 raw dense rank verifier in
tools/verify8_dense_raw.cpp, independently validated the exact
reachability and immediate tactic census through **eight** marked cubes.

The new dense per-color-tier program agrees with these prior exact
published project outputs in each occupancy stratum from 0 to 8
before obtaining the new ninth stratum.

| Occupancy K | Raw reachable board-turn states | D4 root classes | Terminal raw states | Win-in-one D4 puzzle classes |
|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 0 | 0 |
| 1 | 16 | 3 | 0 | 0 |
| 2 | 468 | 60 | 0 | 0 |
| 3 | 11,812 | 1,512 | 0 | 0 |
| 4 | 187,164 | 23,659 | 0 | 0 |
| 5 | 2,055,382 | 258,081 | 0 | 120 |
| 6 | 16,353,436 | 2,048,650 | 552 | 3,674 |
| 7 | 99,693,740 | 12,475,164 | 15,748 | 60,180 |
| 8 | 484,731,202 | 60,627,546 | 247,248 | 634,614 |
| **9 (new)** | **1,927,555,152** | **241,028,313** | **2,500,660** | **4,736,195** |
| **Total through K9** | **2,530,588,373** | **316,462,989** | **2,764,208** | **5,434,783** |

For the immediate-winning puzzle family, **1,942,916** D4 classes
through nine marked cubes have exactly one immediately winning
first legal action.

An independently verified K<=7 three-ply search yields **370**
additional nonterminal root classes with a guaranteed win on the
attacker's second move (and no initial immediate win), of which
**64** have exactly one forcing first action. Since these root
classes are disjoint from the win-in-one family, the new certified
minimum number of distinct tactical puzzles is:

    5,434,783 + 370 = AT LEAST 5,435,153 D4 CLASSES.

Among those, **at least 1,942,980** have exactly one certified
winning first action. Both numbers are lower bounds for larger
horizons and higher occupancies, not an exact global puzzle total.

## Algorithm and a correctness sketch

For a fixed pair (x,o) of numbers of X/O marks, every structurally
possible board with turn is assigned a collision-free combinatorial
rank in the interval

    [0, 2 * C(25,x) * C(25-x,o)).

The first component is the colex rank of the X locations among 25;
the second is the colex rank of O locations among the other 25; the
least-significant bit is the turn. A single bit per possible rank
marks visited canonical D4 states. A queue stores canonical packed
boards for one (x,o) tier at a time. States reached by selecting an
already-marked owned cube remain in the same tier and are propagated
until the queue closes; selecting a blank cube increases exactly one
of x or o, seeding a later tier.

By induction on x+o and the within-tier least fixed point, every
reachable state up to the specified occupancy cap is visited, and
no state beyond that cap can be a predecessor of an in-domain root.
Canonicalization works because all eight D4 symmetries preserve
legal moves, the first X-to-move empty root, and terminal rules.
Counting each orbit by 8 / |stabilizer| independently reconstructs
raw state totals.

This is an exact finite-domain enumeration provided the code
implements those rules; its counts are not samples or extrapolations.
Its own C++ implementation is a separate code path from the original
bitboard/D4 queue and raw enumeration programs. The NEW K9 data
have been executed locally and on GitHub Actions with matching
results, but K9 has not yet been reproduced by a second
independently written *algorithm*. This limitation is intentional.

## Executed evidence and reproducibility

Local Linux g++ -O3, exact K9 full run:
- wall time **499.57 seconds** (elapsed internal 499.072 seconds)
- peak RSS **791,580 KiB** (approx 773 MiB)
- process exit 0, full JSONL summary produced
- source at tools/census5_dual_tier.cpp
- recorded JSONL data at
  benchmarks/census5_dual_color_exact_k9_local.jsonl

GitHub Actions run **41173129941** also compiled the new
independent-tier engine, matched the previously pinned K0..K8
strata, and completed an occupancy-nine traversal with the
same cumulative totals. The GitHub run artifact is named
quixoforge-exact-dual-color-tier-k9.

Reproduce locally:

    c++ -O3 -std=c++17 -Wall -Wextra -pedantic \
        tools/census5_dual_tier.cpp -o /tmp/qf-tiers
    /tmp/qf-tiers 9 > census9.jsonl
    python tools/check_dual_tier_census.py census9.jsonl

The checker requires a complete final end-of-run summary,
checks every previously independent stratum and the new K9
record, recomputes sums, and rejects partial runs.

## Global research boundary

Neither 316,462,989 reachable D4 roots through occupancy nine
nor 5,435,153 certified tactical puzzle classes are the
global full-game totals. The mathematical global upper bound
for all reachable nonterminal positions remains
192,103,543,264 D4 classes. The tighter upper bound on
reachable nonterminal forced-win puzzle classes derived from
Tanaka et al.'s published strong-solve WLD table is
100,535,249,578. See STRONG_SOLVE_PUZZLE_UPPER_BOUND.md.

The game can repeat board-and-turn states, so the number of
complete legal move histories ending in a win is instead
countably infinite in standard Quixo without a repetition cap.
Only the *finite* board-position puzzle classes are the
unsolved global enumeration problem.

Prior research including Robert Shi (2024) already used
two-color tiering and combinatorial hashing; this work
does NOT claim to have invented either concept or to
have strongly solved 5x5 Quixo.
