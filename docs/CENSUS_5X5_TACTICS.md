# QuixoForge — real 5×5 immediate-tactics census (research v1.3)

## Fixed domain, objective and completeness

This is **standard 5×5 two-player Quixo**, X starts, terminal histories stop
immediately, player to move is part of each state. The domain consists of
**every legally reachable position with at most five marked cubes**, including
arbitrarily many same-occupancy moves. The objective is strictly **win on
the next legal move**, with each (selected cube, insertion edge) counted as
a distinct first action. Unrestricted winning strategy, finite-depth
UNKNOWN, draw adjudication, human-rated difficulty and physical puzzle
difficulty are NOT inferred.

The census uses the D4 orbit quotient with X/O colors and turn fixed.
No color-swap quotient is taken. Unique immediate-win means exactly one
winning *legal first action*, not one distinct resulting board.

## Executed local evidence — Python 3.13.5, 30 October 2026

| Occupied cubes | Reachable raw states | D4 position orbits |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 16 | 3 |
| 2 | 468 | 60 |
| 3 | 11,812 | 1,512 |
| 4 | 187,164 | 23,659 |
| **5** | **2,055,382** | **258,081** |
| **0–5** | **2,254,843** | **283,316** |

| One-ply certified objective (occupancy at most five) | Raw states | D4 puzzle classes |
|---|---:|---:|
| At least one immediate winning move | 936 | **120** |
| Exactly one immediate winning move | 360 | **46** |

The count of winning first actions per qualifying orbit is:
1:46, 2:4, 3:30, 4:10, 5:14, 7:8, 8:8.

The full position-orbit-size histogram is:
size 1:1, size 2:13, size 4:2,900, size 8:280,402.
The weighted sum 1+2×13+4×2,900+8×280,402 is 2,254,843.

All 120 qualifying canonical representatives were tested against a
separate pure tuple-array rules oracle, including **all** their possible
first actions. A separate X-first reconstruction independently replayed
legal shortest histories and confirmed all 46 unique-winning examples.
An independent **unsymmetrized raw tuple-state BFS** was then executed
locally in 93.87 seconds (Linux Python 3.13.5), visiting exactly
**2,254,843** states, checking **88,193,892** legal candidate actions and
**17,724,120** retained transitions. Its occupancy histogram agrees in
every layer with the D4 quotient search. The independent oracle is retained
in `tools/verify_5x5_raw.py` and is exercised by the Python 3.13 CI lane.
These are computational observations, not theorem-assistant proofs.

## Why the restricted census is exhaustive

Let occupancy be the number of nonblank cubes. Moving an owned cube
preserves occupancy, while moving a blank cube increases it by exactly
one. Consequently any path to a position with <=5 marks stays at <=5
marks. The empty X-start state is invariant under all eight geometric
symmetries, and every legal move commutes with its D4 image: square
symmetries map insertion paths to insertion paths while leaving player
colors unchanged.

Induction on path length therefore proves that a breadth-first search
over canonical D4 representatives visits **every reachable orbit** in
the declared occupancy domain, provided legal transitions and D4 maps
are correctly implemented. The implementation explores all legal moves
from each representative, including occupancy-preserving cycles, and
never treats an unvisited higher-occupancy state as impossible.

For every reachable nonempty position with occupancy >=2, both players
have at least one mark: the initial X move necessarily places X; the
first O move cannot select an X cube, so it necessarily places O.
Thus terminal five-in-a-row positions cannot occur with <=5 marks.
The earliest immediate-win puzzles inside this domain occur at
occupancy five and can have five or more marked cubes *after* the
winning action. No fabricated terminal-draw adjudication is used.

Orbit-stabilizer supplies each orbit's actual size; dividing a raw
state count by eight without stabilizer correction would be wrong.

## Reproduce

```sh
python -m pip install -e '.[test]'
python -m pytest -q tests/test_census5_tactical.py
python -m quixoforge.census5_tactical --max-stones 5 --verify
python tools/verify_5x5_raw.py --max-stones 5
quixoforge census5 --max-stones 5 --family unique_win_in_one --verify
sha256sum -c SHA256SUMS
```

The first census prints JSON, and family mode prints replayable JSONL
puzzles with canonical 25-cell board, turn, complete solution-action set,
and shortest legal X-first move history. The two-player 3×3 tablebase
is not consulted by this computation.

## Critical open gates and next research

* Independently verify the complete five-cube **D4 orbit quotient** by
  a separate implementation of the eight geometric maps, in addition to
  the now independently reproduced raw reachable-state count.
* Increase exact reachable strata to six occupied cubes, with memory and
  runtime explicitly measured and fail-closed resource limits.
* Add exact bounded D=3 forcing-win and unique-defense objectives with
  two independent AND/OR solvers, separate from unrestricted game values.
* Do not extrapolate the 120 classes into a speculative global total.
* This repository does **not** claim to solve 5×5 Quixo or to validate
  human-rated cognitive difficulty.
