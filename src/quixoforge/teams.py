"""Official four-player team Quixo, including oriented cubes and forced passes.

Seats 0,1,2,3 are positioned clockwise around the table; opposite seats
share a mark.  The orientation stored in a marked cube is the seat toward
which its mark's point faces.  Blank cubes store -1.  The row/column geometry
is fixed: seat numbers describe physical board edges N,E,S,W respectively.

The first *four turns* may only take blank cubes, per Gigamic's first round
rule.  No draw/repetition convention is introduced: forced passes consume a
turn and the game may repeat indefinitely.  Exact history replay establishes
reachability; construction alone does not.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import Move, X, O

BLANK = -1
NORTH, EAST, SOUTH, WEST = range(4)


@dataclass(frozen=True)
class TeamMove:
    """Move a selected edge cube and point its symbol toward a team member."""
    move: Move
    point: int

    def __post_init__(self) -> None:
        if not isinstance(self.move, Move):
            raise ValueError("move must be Move")
        if type(self.point) is not int or self.point not in range(4):
            raise ValueError("point must be a seat 0..3")

    def __str__(self) -> str:
        return f"{self.move}:{self.point}"


@dataclass(frozen=True)
class Pass:
    def __str__(self) -> str:
        return "PASS"


PASS = Pass()
TeamAction = TeamMove | Pass


@dataclass(frozen=True)
class TeamState:
    """Each cell is blank=-1 or points toward an owning seat 0..3."""
    cells: tuple[int, ...]
    seat: int = 0
    ply: int = 0

    def __post_init__(self) -> None:
        if type(self.cells) is not tuple or len(self.cells) != 25 or any(type(c) is not int or c not in (-1, 0, 1, 2, 3) for c in self.cells):
            raise ValueError("25 oriented cube faces (-1 or seat 0..3) required")
        if type(self.seat) is not int or self.seat not in range(4):
            raise ValueError("seat must be 0..3")
        if type(self.ply) is not int or self.ply < 0 or self.seat != self.ply % 4:
            raise ValueError("seat must match ply modulo four")

    @property
    def turn(self) -> int:
        return X if self.seat % 2 == 0 else O

    @property
    def phase(self) -> int:
        return min(self.ply, 4)

    def marks(self) -> tuple[int, ...]:
        return tuple(0 if c == BLANK else X if c % 2 == 0 else O for c in self.cells)


def initial() -> TeamState:
    return TeamState((BLANK,) * 25)


def winner(s: TeamState) -> int | None:
    """If both marks line up, the previous mover loses, even on a double line."""
    if not isinstance(s, TeamState):
        raise TypeError("expected TeamState")
    b = s.cells
    lines: set[int] = set()
    for indices in ([5*r+c for c in range(5)] for r in range(5)):
        vals = [b[i] for i in indices]
        if all(v != BLANK and v % 2 == vals[0] % 2 for v in vals):
            lines.add(X if vals[0] % 2 == 0 else O)
    for indices in ([5*r+c for r in range(5)] for c in range(5)):
        vals = [b[i] for i in indices]
        if all(v != BLANK and v % 2 == vals[0] % 2 for v in vals):
            lines.add(X if vals[0] % 2 == 0 else O)
    for indices in ([6*j for j in range(5)], [4+4*j for j in range(5)]):
        vals = [b[i] for i in indices]
        if all(v != BLANK and v % 2 == vals[0] % 2 for v in vals):
            lines.add(X if vals[0] % 2 == 0 else O)
    if len(lines) == 2:
        return s.turn
    return next(iter(lines)) if lines else None


def legal_moves(s: TeamState) -> tuple[TeamAction, ...]:
    if winner(s) is not None:
        return ()
    moves: list[TeamAction] = []
    for i, mark in enumerate(s.cells):
        r, c = divmod(i, 5)
        if 0 < r < 4 and 0 < c < 4:
            continue
        if mark != BLANK and (s.ply < 4 or mark != s.seat):
            continue
        for edge, allowed in (("L", c > 0), ("R", c < 4), ("U", r > 0), ("D", r < 4)):
            if allowed:
                for point in (s.seat, (s.seat + 2) % 4):
                    moves.append(TeamMove(Move(i, edge), point))
    return tuple(moves) if moves else (PASS,)


def apply(s: TeamState, action: TeamAction) -> TeamState:
    if action not in legal_moves(s):
        raise ValueError(f"illegal four-player action: {action!r}")
    if action == PASS:
        return TeamState(s.cells, (s.seat + 1) % 4, s.ply + 1)
    r, c = divmod(action.move.index, 5)
    if action.move.edge == "L":
        path = [5*r+j for j in range(c, -1, -1)]
    elif action.move.edge == "R":
        path = [5*r+j for j in range(c, 5)]
    elif action.move.edge == "U":
        path = [5*j+c for j in range(r, -1, -1)]
    else:
        path = [5*j+c for j in range(r, 5)]
    board = list(s.cells)
    for dst, src in zip(path, path[1:]):
        board[dst] = board[src]
    board[path[-1]] = action.point
    return TeamState(tuple(board), (s.seat + 1) % 4, s.ply + 1)


def replay(actions: Iterable[TeamAction]) -> TeamState:
    state = initial()
    for a in actions:
        state = apply(state, a)
    return state


class FourPlayerGame:
    """Adapter to the existing generic, three-valued finite-horizon solver."""
    def legal_moves(self, s: TeamState) -> tuple[TeamAction, ...]:
        return legal_moves(s)

    def apply(self, s: TeamState, m: TeamAction) -> TeamState:
        return apply(s, m)

    def winner(self, s: TeamState) -> int | None:
        return winner(s)

    def turn(self, s: TeamState) -> int:
        return s.turn

    def cache_key(self, s: TeamState) -> tuple:
        # Beyond the first round, the absolute ply does not affect rules.
        return (s.cells, s.seat, s.phase)
