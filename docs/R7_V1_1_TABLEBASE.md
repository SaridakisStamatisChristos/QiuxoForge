# QuixoForge v1.1 — exact 3x3 strong solution and reproduction ledger

## Contract

Ship a self-contained, actually installable 3x3 lookup database covering *every reachable state*, independently produced by two distinct game transition engines and an exhaustive cyclic retrograde solver. Preserve the official 5x5 and 4-player engine APIs unchanged. No false claim of a new 5x5 solution.

## Fixed research problem

3×3 board, 3-in-row wins; X moves first. Perimeter cube blank/own extraction, push to a distinct row/column end, alternate turns, and opponent-win precedence if a move creates simultaneous X/O lines. All play histories stop on a winning terminal board. The full graph is finite, including repeat-cycle transitions. Attractor retrograde uses `NONFORCED` for positions from which terminal victory cannot be forced, **not** an invented official repetition draw.

## Executed mathematical evidence (local Linux Python 3.13)

| Independent measurement | Result |
|---|---:|
| Tuple-reference full reachable states | 32,027 |
| Bitmask-optimized full reachable states | 32,027 |
| Full directed move transitions, each model | 276,936 |
| States and every adjacency list equal under conversion | Yes |
| Value/remoteness equality for every state | Yes |
| WIN states | 20,247 |
| LOSS states | 11,780 |
| NONFORCED states | 0 |
| X-first empty opening | WIN in 7 plies |
| 3x3 tablebase compressed bytes | 82,795 |
| Compressed data SHA256 | `6ad95cb58dd78e675bed99136ea73dbc9c1507a85bd198ef154640dabf015eae` |
| Uncompressed binary SHA256 | `ba8e0399f38cbc5ea48140e5201ef0c0d7a435f95aad4db245305df93fbc23ad` |

The identity of state count and initial remoteness matches Shi (2024), section 7.4.3; the other counts and checksums are newly measured reproducibility observations, not claimed novel theoretical results.

## Evidence commands

```sh
python -m pip install -e '.[test]'
python -m pytest -q
python -m quixoforge.tablebase
python -m quixoforge.tablebase --rebuild
quixoforge micro --board ......... --turn X
sha256sum -c SHA256SUMS
```

`--rebuild` independently enumerates both complete graphs and checks each state, outcome and remoteness, each edge and the committed compressed blob checksum. Unit tests independently check all 32,027 packed Bellman equations from the bitboard oracle and all 8×32,027 D4 rotations/reflections. `micro` returns exact optimal actions for *reachable 3x3 states only*, rejecting unreachable queries instead of inventing a heuristic answer.

## R7 evidence and remaining boundaries

- `R19 / VERIFIED`: 2..5-sized variant rules work on tested legal random trajectories with reference/bitboard parity; complete 3x3 universe independently reconstructed.
- `R20 / VERIFIED`: finite game retrograde solver, explicit state cap failure, terminal/cycle edge cases, a second full-graph checker.
- `R21 / VERIFIED local`: shipped packaged tablebase with fixed digest and runtime integrity checks; tested opening policy and corrupt/stale/illegal queries.
- `R22 / UNVERIFIED until CI`: Python 3.10 and 3.13 wheel/rebuild jobs must pass on GitHub SHA.
- `C1 / NOT CLAIMED`: our own 4x4 or 5x5 strong solve. 5x5 was already published as draw by Tanaka et al. (2020), independently by Shi (2024).
- `C2 / NOT CLAIMED`: dominance against external Quixo engines; local tests do not establish Elo.
- `C3 / NOT CLAIMED`: complete four-player mathematical solve, human difficulty rating, or a formal Lean/Coq proof of Python implementation.

## Sources

Tanaka, Bonnet, Tixeuil, Tamura (2020), *Quixo Is Solved*, https://arxiv.org/abs/2007.15895

Shi (2024), *Parallel Solving of Two-Player Tierable Abstract Strategy Games*, UCB/EECS-2024-139, https://www2.eecs.berkeley.edu/Pubs/TechRpts/2024/EECS-2024-139.pdf
