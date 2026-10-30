# QuixoForge — complete finite-domain 5×5 census through eight occupied cubes (R7 v1.4)

## Existing solution literature and novelty limits

The original two-player 5×5 Quixo game was strongly solved by
Tanaka et al. (*Quixo Is Solved*, 2020/2022,
https://arxiv.org/abs/2007.15895).
Robert Shi, *Parallel Solving of Two-Player Tierable Abstract
Strategy Games* (U.C. Berkeley, 2024), Chapter 7.2,
https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-139.pdf,
already describes the monotone (blank,X,O) tiers and their
combinatorial hashing. **We do not claim to have invented Quixo tiering,
combinatorial hashes, the solution to Quixo, or proof-number search.**
This project's separate, more narrowly scoped research result is the
independently reproduced **legally reachable, nonterminal, geometrically
unique immediate-tactical puzzle census**, with additional complete
three-ply positive certificates.

## Scientific contract

The goal is counting mathematically distinct, meaningful, verifiable **standard two-player 5×5 Quixo puzzles**, not solving the game again. X begins on a blank board; each state records board markings and side to move. Histories stop immediately on a winning position. A first action is a selected eligible perimeter cube plus insertion end. D4 rotational/reflection equivalence preserves X/O and side to move; color exchange is **not** treated as an equivalence.

A **win-in-one puzzle** is a legally reachable nonterminal root position where the player to move has at least one legal first action that wins immediately. **Unique win-in-one** requires exactly one winning first action, not one eventual perfect-play winning move. This is an operational mathematical puzzle family; human-rated meaningfulness remains an independent open question.

## Exact enumerated domain and first-action classifications

All numerical counts in this table are outputs of the native exhaustive D4 quotient BFS. The entire ≤7 raw reachable graph and the one-ply winning-action classifications are separately reproduced by an unsymmetrized tuple-array BFS with collision-free combinatorial ranking.

| Occupancy | Reachable raw states | Reachable D4 classes | Terminal D4 classes | Win-in-one D4 classes | Unique win-in-one D4 |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 0 | 0 | 0 |
| 1 | 16 | 3 | 0 | 0 | 0 |
| 2 | 468 | 60 | 0 | 0 | 0 |
| 3 | 11,812 | 1,512 | 0 | 0 | 0 |
| 4 | 187,164 | 23,659 | 0 | 0 | 0 |
| 5 | 2,055,382 | 258,081 | 0 | 120 | 46 |
| 6 | 16,353,436 | 2,048,650 | 80 | 3,674 | 1,202 |
| 7 | 99,693,740 | 12,475,164 | 2,070 | 60,180 | 20,283 |
| 8 | 484,731,202 | 60,627,546 | 31,291 | 634,614 | 222,426 |
| **Total ≤8** | **603,033,221** | **75,434,676** | **33,441** | **698,588** | **243,957** |

Raw winning-root counts: K5 936 (unique 360); K6 29,140 (unique 9,508); K7 480,424 (unique 161,920); K8 5,071,268 (unique 1,777,204); total ≤8: 5,581,768 (unique 1,948,992).

## Independent verification

The standalone native D4 enumerator (tools/census5_native.cpp) uses packed X/O masks and all 44 legal actions, checks terminal rules, and weights each representative by its actual orbit size. Local runs of tested development variants: K5 0.44s (~15.8MB); K6 7.55s (~119.5MB); K7 31.83s (~379.4MB), Linux g++14.2, -O3. These are not equivalent-workload speed comparisons.

The separate native raw verifier (tools/verify5_native_raw.cpp) contains its **own tuple-array move and winner implementations**, no symmetry quotient and no dependency on the QuixoForge rules. At K6 it enumerated **18,608,279 raw states**, of which **552 are terminal**, examining **713,951,292 legal actions** and retaining **178,424,208** within-domain transitions; local runtime ~31.11s and memory ~409MB. It also matches all previously reproduced K≤5 layers. The machine checker tools/check_native_census.py compares the independent raw and D4 outputs, exact occupancy tables, Burnside partitions, terminal strata and recorded first-action families.

An additional, entirely unsymmetrized seven-cube dense-rank verifier (tools/verify7_dense_raw.cpp) has now enumerated 118,302,019 raw states, 16,300 terminal states, 4,449,658,784 legal candidate actions and 1,342,280,992 in-domain transitions. Its independently implemented list-shift and winner checks also found exactly 510,500 raw immediate-win positions and 171,788 raw unique-win positions, matching all occupancy layers. The 195.47-second local C++17 run peaked near 944 MiB RAM. This is independent computational corroboration of the native D4 class counts via orbit-stabilizer, not a formal proof of implementation correctness.

For the restricted root domain K≤5, a separate Python fast threat-preimage evaluator classified all **132,116** potentially relevant roots (own marks ≥3). It found no additional forced-win-in-exactly-three positions beyond immediate wins. This result is a finite-horizon computational claim pending its distinct CI/differential gate; no later tactical continuation is occupancy-capped.

## Completeness proof within an occupancy cap

Let h(s) be the number of marked cells in a board. Every legal move either extracts a marked cube and preserves h or extracts a blank cube and increases h by exactly one. Therefore h never decreases. Every path to a state with h≤K stays in the induced domain h≤K, even if a path performs arbitrarily many mark-preserving actions. BFS from the fixed X-first root, expanding all legal in-domain moves and stopping at terminals, therefore discovers every legally reachable state within the cap.

Every square rotation/reflection preserves extraction eligibility, insertion paths, turn, winner, and h, while fixing the empty initial state. Thus it induces an automorphism of the reachable state graph. Inductively, BFS on one representative per D4 orbit discovers exactly all reachable orbits. Orbit-stabilizer proves that each representative contributes 8 divided by its stabilizer size to the raw count; not all orbits have eight states. Terminal outcomes must be checked explicitly from occupancy six onward.

The Python three-ply AND/OR solver in quixoforge.census5_forced3 is not a globally solved game. Its algebraic first-action threats invert each of 44 insertion mappings against each of the twelve winning lines; every potential winning child is then checked by the actual winner rule. A first action qualifies as forcing by ply three if every legal defender response either already loses or permits an immediate winning attacker reply. This is necessary and sufficient for this *finite* tactical horizon.

## Eight-cube native extension and independent-verifier scope

The optimized native implementation has additionally traversed all
K≤8 reachable 5×5 states: **603,033,221** raw board/turn positions
in **75,434,676** D4 classes, with **698,588** geometrically distinct
win-in-one classes, **243,957** of which have exactly one immediately
winning legal first action. The exactly-eight-cube layer contains
484,731,202 states, 60,627,546 position classes, 31,291 terminal
classes, 634,614 immediate-win classes, and 222,426 unique-win classes.

The native K8 run completed locally in 247.984 seconds with
1,639,552 KiB observed maximum RSS. A completely separate full raw
K8 enumeration (tools/verify8_dense_raw.cpp) uses 32-bit
collision-free combinadic state ranks and an exact visited bitset.
**Its complete independent traversal FINISHED successfully:**
603,033,221 states, 263,548 terminal states, 5,581,768 raw win-one
positions and 1,948,992 raw unique-win-one positions. Every occupancy
layer agreed with the independent native D4 search. It checked
22,219,777,004 legal candidate actions, retained 7,896,591,036
in-domain transitions, ran in 1,294.7s, and peaked at 2,443,136 KiB
RSS. The output is committed at
benchmarks/census_5x5_k8_raw_independent.json.
Final GitHub CI evidence remains a separate release gate.

A second mathematical invariant gives a structural upper bound for
*every* occupancy, independently of reachability. Let [x^k] denote
the k-th ordinary polynomial coefficient. Then

```text
B_k = [x^k] (
  (1+2x)^25 + 2(1+2x)(1+2x^4)^6
  + (1+2x)(1+2x^2)^12
  + 4(1+2x)^5(1+2x^2)^10
) / 4
```

counts all structurally possible (board,turn) D4 orbits with k
occupied cubes. **B_8 = 69,278,970**, so the native K8 reachable
count 60,627,546 lies below its independently derived upper bound.
All 26 coefficients are produced by tools/structural_orbit_bounds.py.

Furthermore, each player's mark count is separately monotone.
See docs/TWO_COLOR_LAYER_SATURATION_THEOREM.md for the proved
exact two-dimensional fixed-point layer recurrence, which enables
out-of-core or parallel census beyond the current RAM-limited regime.

## New multi-ply seven-cube puzzle family

An exhaustive local native attacker/defender/attacker AND/OR classifier
(`tools/census5_force3_native.cpp`) has independently examined all
14,807,130 reachable geometric root classes at occupancy <=7 and
identified **370** geometrically distinct **new forcing-win-by-three**
puzzle classes (2,880 raw board/turn states). These exclude roots with
any immediate winning legal action. **64** of the 370 classes (512 raw
states) have exactly one forcing first legal action.

For every candidate forcing action, the attacker must win after every
defender response within three plies; neither defender nor attacker
continuations are occupancy-capped. The native enumerator emits the
complete 370 geometric root bitmasks with the claimed number of
forcing first actions; `tools/verify_force3_positives.py`
independently replays every first/defense/final action using a completely
separate Python tuple-array rules implementation and checks D4 orbit
uniqueness. **All 370 positive root certificates independently passed**
(5.88s, 104,208 KiB max RSS). The forcing first-action multiplicity
histogram is 1:64, 2:120, 3:120, 4:66; weighted raw states total 2,880.
A further independent check established that **all 370** have an
**adaptive-response** property: there exist two different legal defender
replies whose sets of winning final legal actions are *disjoint*.
Consequently, no single fixed second attacker action wins against
both replies. All **64 unique-first-action** classes share this
property. The independently verified adaptive-first-action histogram
is 1:64, 2:120, 3:120, 4:66. This is a stronger tactical definition
than win-in-three alone, but it is not a human difficulty score.

The exhaustive negative classification still depends on the separate
native graph traversal, and final-head CI is a distinct release gate.

For K<=5 and K<=6 roots, the corresponding exact three-ply search
found zero additional forcing puzzle classes beyond win-in-one roots.
This is a finite-horizon fact, not a global perfect-play claim.

## Global mathematical bounds, and the unsolved census

Burnside on all 25-cell colorings yields exactly 105,918,450,471 D4 coloring classes; with both possible players to move, an upper bound of **211,836,900,942** board-turn classes, many unreachable. The independently reproduced K≤7 census establishes **21,531 unique-win-in-one** geometric classes, and the additional native-computed K8 layer raises the current full-board lower-bound candidate to **243,957 classes**, conditional on the documented rules and D4 group action. It does **not** determine the global exact number of reachable winning puzzles, all finite-depth puzzles, eventual unique wins, or subjectively meaningful human puzzles. Do not extrapolate percentages or label these counts the global answer.

## One-command reproducibility and evidence checks

~~~sh
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/census5_native.cpp -o /tmp/qf-census5
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify5_native_raw.cpp -o /tmp/qf-raw5
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify7_dense_raw.cpp -o /tmp/qf-raw7
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify8_dense_raw.cpp -o /tmp/qf-raw8
/tmp/qf-census5 5 > /tmp/qf-k5.json
/tmp/qf-census5 6 > /tmp/qf-k6.json
/tmp/qf-census5 7 20000000 > /tmp/qf-k7.json
/tmp/qf-census5 8 100000000 > /tmp/qf-k8.json
/tmp/qf-raw5 6 > /tmp/qf-raw6.json
/tmp/qf-raw7 7 125000000 > /tmp/qf-raw7.json
/tmp/qf-raw8 8 700000000 > /tmp/qf-raw8.json
python tools/check_native_census.py --k5 /tmp/qf-k5.json --k6 /tmp/qf-k6.json --k7 /tmp/qf-k7.json --k8 /tmp/qf-k8.json --raw6 /tmp/qf-raw6.json --raw7 /tmp/qf-raw7.json --raw8 /tmp/qf-raw8.json
python -m quixoforge.census5_forced3 --verify
python -m pytest -q
sha256sum -c SHA256SUMS
~~~

Invalid occupancy caps or resource budgets fail instead of returning a misleading partial census.

## UCS-Pro R7 evidence and requirement ledger

| Requirement | Evidence status | Critical limitation |
|---|---|---|
| 5×5 official board, move and terminal semantics | VERIFIED for K≤5 against independent Python implementation | Now independently reproduced through K7, including complete negative classifications |
| Reachability K≤6 | VERIFIED by native D4 and independent raw tuple BFS | Exact only within declared occupancy |
| Reachability K=7 | VERIFIED via two independent exhaustive native graph traversals | Exact within the declared K≤7 domain only |
| Reachability and immediate-win classification K=8 | VERIFIED locally with two independently implemented full-state enumerators and classifiers | CI final-head evidence pending; never a global full-game count |
| Immediate-win objective K≤5 | VERIFIED by multiple independently implemented paths | Does not imply eventual forced-win strategy |
| Immediate-win objective K6–7 | VERIFIED by independently classified raw winning-action counts and D4 partition | Still not eventual game-theoretic strategy |
| Three-ply K≤5 roots | COMPUTED with fast preimage/AND-OR algorithm | CI and independent negative-certificate validation pending |
| Global exact meaningful-puzzle total | UNVERIFIED | Operational puzzle-family definition and near-full occupancy enumeration still required |
| Re-solving Quixo; GUI; auth/infra | N/A | Outside this headless research mission |

The raw seven-cube classifier is independently replicated and the full reproducibility command checks both engines. This is a finite-domain census with explicit scope, **not a claim of a solved global 5×5 puzzle census**.
