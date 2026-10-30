"""Pure, immutable and deliberately conservative Quixo state representation.

Structural validation is NOT a proof of historical reachability. A replayed legal
move sequence *is* a constructive reachability witness.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

N = 5
EMPTY, X, O = 0, 1, -1
DIRS = ("L", "R", "U", "D")


@dataclass(frozen=True, order=True)
class Move:
    index: int
    edge: str

    def __post_init__(self) -> None:
        if type(self.index) is not int or not 0 <= self.index < 25:
            raise ValueError("move index must be integer in [0, 24]")
        if self.edge not in DIRS:
            raise ValueError("edge must be L, R, U or D")

    def __str__(self) -> str:
        return f"{self.index}:{self.edge}"

    @classmethod
    def parse(cls, token: str) -> "Move":
        left, sep, right = token.partition(":")
        if not sep or not left.isdecimal():
            raise ValueError(f"invalid move: {token!r}")
        return cls(int(left), right)


@dataclass(frozen=True)
class State:
    cells: tuple[int, ...]
    turn: int = X

    def __post_init__(self) -> None:
        if type(self.cells) is not tuple or len(self.cells) != 25 or any(type(v) is not int or v not in (EMPTY, X, O) for v in self.cells):
            raise ValueError("cells must be exactly 25 integers from {-1,0,1}")
        if type(self.turn) is not int or self.turn not in (X, O):
            raise ValueError("turn must be X=1 or O=-1")

    def __str__(self) -> str:
        symbols = {X: "X", O: "O", EMPTY: "."}
        return "\n".join("".join(symbols[v] for v in self.cells[r*5:r*5+5]) for r in range(5))


def initial(start: int = X) -> State:
    if type(start) is not int or start not in (X, O):
        raise ValueError("start must be X or O")
    return State((EMPTY,) * 25, start)


def replay(moves: Iterable[Move], start: int = X) -> State:
    """Exact constructive legality certificate; rejects any move after a win."""
    from .reference import apply
    position = initial(start)
    for move in moves:
        position = apply(position, move)
    return position


def validate_history(state: State, moves: Iterable[Move], start: int = X) -> bool:
    """True iff this complete history actually produces the supplied state."""
    return replay(moves, start) == state
