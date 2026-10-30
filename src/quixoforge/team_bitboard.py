"""Independent four-player bitmask transitions and terminal detection.

Four mutually exclusive 25-bit oriented masks, one per physical seat.
No calls to the high-level team implementation are used to move cubes.
A structural position may be unreachable; history replay must establish that.
"""
from __future__ import annotations
from dataclasses import dataclass
from .model import Move, X, O
from .bitboard import FULL, PATHS, LINE_MASKS
from .teams import TeamState, TeamMove, TeamAction, PASS


@dataclass(frozen=True)
class TeamBits:
    points: tuple[int, int, int, int]
    seat: int
    ply: int

    def __post_init__(self):
        if type(self.points) is not tuple or len(self.points) != 4 or any(type(p) is not int or p < 0 or p & ~FULL for p in self.points):
            raise ValueError("four nonnegative 25-bit seat masks required")
        if any(self.points[i] & self.points[j] for i in range(4) for j in range(i+1, 4)):
            raise ValueError("oriented masks overlap")
        if type(self.ply) is not int or self.ply < 0 or type(self.seat) is not int or self.seat not in range(4) or self.seat != self.ply % 4:
            raise ValueError("invalid seat / ply")

    @classmethod
    def from_state(cls, s: TeamState) -> "TeamBits":
        return cls(tuple(sum((1 << i) for i, p in enumerate(s.cells) if p == seat) for seat in range(4)), s.seat, s.ply)

    def state(self) -> TeamState:
        return TeamState(tuple(next((k for k, mask in enumerate(self.points) if mask & (1 << i)), -1) for i in range(25)), self.seat, self.ply)

    @property
    def turn(self) -> int:
        return X if self.seat % 2 == 0 else O

    @property
    def phase(self) -> int:
        return min(self.ply, 4)


def winner(b: TeamBits) -> int | None:
    even = b.points[0] | b.points[2]
    odd = b.points[1] | b.points[3]
    x = any(even & line == line for line in LINE_MASKS)
    o = any(odd & line == line for line in LINE_MASKS)
    if x and o:
        return b.turn
    return X if x else O if o else None


def legal_moves(b: TeamBits) -> tuple[TeamAction, ...]:
    if winner(b) is not None:
        return ()
    used = b.points[0] | b.points[1] | b.points[2] | b.points[3]
    chosen = (FULL & ~used) | (b.points[b.seat] if b.ply >= 4 else 0)
    choices = (b.seat, (b.seat + 2) % 4)
    moves = tuple(TeamMove(m, point) for m in PATHS if chosen & (1 << m.index) for point in choices)
    return moves or (PASS,)


def apply(b: TeamBits, action: TeamAction) -> TeamBits:
    if action not in legal_moves(b):
        raise ValueError("illegal four-player bitboard move")
    if action == PASS:
        return TeamBits(b.points, (b.seat + 1) % 4, b.ply + 1)
    path = PATHS[action.move]
    shifted = [0] * 4
    removed = sum(1 << idx for idx in path)
    for orientation, mask in enumerate(b.points):
        bits = mask & ~removed
        for dst, src in zip(path, path[1:]):
            if mask & (1 << src):
                bits |= 1 << dst
        shifted[orientation] = bits
    shifted[action.point] |= 1 << path[-1]
    return TeamBits(tuple(shifted), (b.seat + 1) % 4, b.ply + 1)


class BitboardFourPlayerGame:
    """Optimized four-player adapter for generic exact bounded proof searches."""
    def legal_moves(self, s: TeamBits) -> tuple[TeamAction, ...]: return legal_moves(s)
    def apply(self, s: TeamBits, move: TeamAction) -> TeamBits: return apply(s, move)
    def winner(self, s: TeamBits) -> int | None: return winner(s)
    def turn(self, s: TeamBits) -> int: return s.turn
    def cache_key(self, s: TeamBits) -> tuple: return (*s.points, s.seat, s.phase)
