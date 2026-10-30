# QuixoForge

[![Python tests](https://github.com/SaridakisStamatisChristos/QiuxoForge/actions/workflows/ci.yml/badge.svg)](https://github.com/SaridakisStamatisChristos/QiuxoForge/actions/workflows/ci.yml)

**A correctness-first, headless, two-player Quixo research engine.** Built with UCS-Pro R7 contract/evidence discipline. No UI, service, or infrastructure dependencies.

The name of this repository is `QiuxoForge` (as requested); the importable Python package and project name are `quixoforge`.

## Capabilities

- Exact **two-player** official rules: perimeter cube selection, disallow opponents' marks, shift toward the removed cube, reinsert at a *different* extremity, 12 lines, no pass, opponent-line priority on simultaneous wins, and halt after victory.
- Immutable 25-cell board states and exact legal-history replay. An arbitrary structurally valid board is **not** asserted reachable.
- Independent reference list-shift and bitboard transition/win implementations, tested through exhaustive two-ply opening tree and seeded legal playouts.
- Full D4 (dihedral) rotations/reflections; canonical transposition keys (board geometry only, no color-swap shortcut).
- Exact **finite-horizon** 3-valued solvers: `WIN`, `LOSS`, `UNKNOWN`. They do *not* purport to solve Quixo globally; no repetition/draw rule is fabricated.
- AND/OR certificates with an independent checker validating every defense on a LOSS node and a concrete winning move on a WIN node.
- Two replay-certified, uniquely solved tactical puzzles: immediate win (depth 1), short forcing win (minimal depth 3).
- Configurable deterministic comparative benchmark; no guaranteed speed superiority. Pluggable `FiniteGame` protocol for further abstract strategy games.

## One-command tests and checks

```bash
python -m pip install -e '.[test]'
python -m pytest -q
python -m quixoforge.verify_examples
python -m quixoforge.bench --seed 711 --count 8 --plies 9 --depth 2 --repeats 3
```

Use `quixoforge show 0:R 5:D`, `quixoforge solve --depth 2 0:R 5:D`, or `quixoforge puzzle --depth 3 <history>` for a minimal headless interface. `index:edge` uses row-major indices `0..24` and `L/R/U/D` as the **insertion extremity**, not the direction the selected cube moves.

## Correctness and research scope

See [rules and proof obligations](docs/RESEARCH.md) and the [R7 evidence/assumption ledger](docs/EVIDENCE.md). The two-player rules are grounded in the [Gigamic official rulebook](https://export.gigamic.com/wp-content/uploads/2021/01/INS-RULES_QUIXO_03-2017.pdf), English page 4 (PDF page index 1). The four-player team variant has additional point-orientation requirements and is **not implemented**; neither are human announcement/tournament timing, solved opening tablebases, full reachability decisions for arbitrary boards, or a game-theoretic solution to infinite play. These are explicit scope limitations rather than silent claims.

The tactical puzzles are provable **relative to the formalized two-player move model and a stated finite horizon**, with machine-checkable finite proof trees. A verified finite-horizon result is not an unbounded theorem about optimal play.

## License

MIT. Quixo is a game by Thierry Chapeau, published by Gigamic; this independent engine does not contain the official rulebook or copyrighted game assets.
