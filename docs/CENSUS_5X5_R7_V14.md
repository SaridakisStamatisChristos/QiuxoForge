# QuixoForge — complete finite-domain 5×5 census through seven occupied cubes (R7 v1.4)

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
| **Total ≤7** | **118,302,019** | **14,807,130** | **2,150** | **63,974** | **21,531** |

Raw winning-root counts: K5 936 (unique 360); K6 29,140 (unique 9,508); K7 480,424 (unique 161,920); total 510,500 (unique 171,788).

## Independent verification

The standalone native D4 enumerator (tools/census5_native.cpp) uses packed X/O masks and all 44 legal actions, checks terminal rules, and weights each representative by its actual orbit size. Local runs of tested development variants: K5 0.44s (~15.8MB); K6 7.55s (~119.5MB); K7 31.83s (~379.4MB), Linux g++14.2, -O3. These are not equivalent-workload speed comparisons.

The separate native raw verifier (tools/verify5_native_raw.cpp) contains its **own tuple-array move and winner implementations**, no symmetry quotient and no dependency on the QuixoForge rules. At K6 it enumerated **18,608,279 raw states**, of which **552 are terminal**, examining **713,951,292 legal actions** and retaining **178,424,208** within-domain transitions; local runtime ~31.11s and memory ~409MB. It also matches all previously reproduced K≤5 layers. The machine checker tools/check_native_census.py compares the independent raw and D4 outputs, exact occupancy tables, Burnside partitions, terminal strata and recorded first-action families.

For the restricted root domain K≤5, a separate Python fast threat-preimage evaluator classified all **132,116** potentially relevant roots (own marks ≥3). It found no additional forced-win-in-exactly-three positions beyond immediate wins. This result is a finite-horizon computational claim pending its distinct CI/differential gate; no later tactical continuation is occupancy-capped.

## Completeness proof within an occupancy cap

Let h(s) be the number of marked cells in a board. Every legal move either extracts a marked cube and preserves h or extracts a blank cube and increases h by exactly one. Therefore h never decreases. Every path to a state with h≤K stays in the induced domain h≤K, even if a path performs arbitrarily many mark-preserving actions. BFS from the fixed X-first root, expanding all legal in-domain moves and stopping at terminals, therefore discovers every legally reachable state within the cap.

Every square rotation/reflection preserves extraction eligibility, insertion paths, turn, winner, and h, while fixing the empty initial state. Thus it induces an automorphism of the reachable state graph. Inductively, BFS on one representative per D4 orbit discovers exactly all reachable orbits. Orbit-stabilizer proves that each representative contributes 8 divided by its stabilizer size to the raw count; not all orbits have eight states. Terminal outcomes must be checked explicitly from occupancy six onward.

The Python three-ply AND/OR solver in quixoforge.census5_forced3 is not a globally solved game. Its algebraic first-action threats invert each of 44 insertion mappings against each of the twelve winning lines; every potential winning child is then checked by the actual winner rule. A first action qualifies as forcing by ply three if every legal defender response either already loses or permits an immediate winning attacker reply. This is necessary and sufficient for this *finite* tactical horizon.

## Global mathematical bounds, and the unsolved census

Burnside on all 25-cell colorings yields exactly 105,918,450,471 D4 coloring classes; with both possible players to move, an upper bound of **211,836,900,942** board-turn classes, many unreachable. The independently reproduced K≤7 census establishes **21,531 unique-win-in-one** geometric classes as a rigorous computational lower bound for the full game, conditional on the documented rules and D4 group action. It does **not** determine the global exact number of reachable winning puzzles, all finite-depth puzzles, eventual unique wins, or subjectively meaningful human puzzles. Do not extrapolate percentages or label these counts the global answer.

## One-command reproducibility and evidence checks

~~~sh
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/census5_native.cpp -o /tmp/qf-census5
c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify5_native_raw.cpp -o /tmp/qf-raw5
/tmp/qf-census5 5 > /tmp/qf-k5.json
/tmp/qf-census5 6 > /tmp/qf-k6.json
/tmp/qf-census5 7 20000000 > /tmp/qf-k7.json
/tmp/qf-raw5 6 > /tmp/qf-raw6.json
python tools/check_native_census.py --k5 /tmp/qf-k5.json --k6 /tmp/qf-k6.json --k7 /tmp/qf-k7.json --raw6 /tmp/qf-raw6.json
python -m quixoforge.census5_forced3 --verify
python -m pytest -q
sha256sum -c SHA256SUMS
~~~

Invalid occupancy caps or resource budgets fail instead of returning a misleading partial census.

## UCS-Pro R7 evidence and requirement ledger

| Requirement | Evidence status | Critical limitation |
|---|---|---|
| 5×5 official board, move and terminal semantics | VERIFIED for K≤5 against independent Python implementation | Independent K6–7 terminal/first-action audit is still valuable |
| Reachability K≤6 | VERIFIED by native D4 and independent raw tuple BFS | Exact only within declared occupancy |
| Reachability K=7 | VERIFIED via two independent exhaustive native graph traversals | Exact within the declared K≤7 domain only |
| Immediate-win objective K≤5 | VERIFIED by multiple independently implemented paths | Does not imply eventual forced-win strategy |
| Immediate-win objective K6–7 | VERIFIED by independently classified raw winning-action counts and D4 partition | Still not eventual game-theoretic strategy |
| Three-ply K≤5 roots | COMPUTED with fast preimage/AND-OR algorithm | CI and independent negative-certificate validation pending |
| Global exact meaningful-puzzle total | UNVERIFIED | Operational puzzle-family definition and near-full occupancy enumeration still required |
| Re-solving Quixo; GUI; auth/infra | N/A | Outside this headless research mission |

The raw seven-cube classifier is independently replicated and the full reproducibility command checks both engines. This is a finite-domain census with explicit scope, **not a claim of a solved global 5×5 puzzle census**.
