"""Independent transition path: 25-bit X/O occupancy and precomputed shifts.

Neither legal_move generation nor winner nor transition calls the reference
implementation; differential tests compare the two semantic paths.
"""
from __future__ import annotations
from dataclasses import dataclass
from .model import State, Move, X, O
from .symmetry import D4

FULL = (1 << 25) - 1
LINE_MASKS = tuple(
    [sum(1 << (r*5+c) for c in range(5)) for r in range(5)]
    + [sum(1 << (r*5+c) for r in range(5)) for c in range(5)]
    + [sum(1 << (6*i) for i in range(5)), sum(1 << (4+4*i) for i in range(5))]
)


def _paths() -> dict[Move, tuple[int, ...]]:
    p = {}
    for i in range(25):
        r, c = divmod(i, 5)
        if r not in (0, 4) and c not in (0, 4):
            continue
        for edge, choices in (("L", [(r, j) for j in range(c, -1, -1)]),
                              ("R", [(r, j) for j in range(c, 5)]),
                              ("U", [(j, c) for j in range(r, -1, -1)]),
                              ("D", [(j, c) for j in range(r, 5)])):
            if len(choices) > 1:
                p[Move(i, edge)] = tuple(a*5+b for a,b in choices)
    assert len(p) == 44
    return p

PATHS = _paths()


@dataclass(frozen=True)
class Bits:
    x: int
    o: int
    turn: int

    def __post_init__(self):
        if type(self.x) is not int or type(self.o) is not int or self.x < 0 or self.o < 0:
            raise ValueError("bitboards must be nonnegative integers")
        if (self.x | self.o) & ~FULL or self.x & self.o:
            raise ValueError("overlapping/out-of-range stones")
        if type(self.turn) is not int or self.turn not in (X, O):
            raise ValueError("invalid side to move")

    @classmethod
    def from_state(cls, s: State) -> "Bits":
        x = sum(1 << i for i,v in enumerate(s.cells) if v == X)
        o = sum(1 << i for i,v in enumerate(s.cells) if v == O)
        return cls(x, o, s.turn)

    def state(self) -> State:
        return State(tuple(X if (self.x >> i)&1 else O if (self.o >> i)&1 else 0 for i in range(25)), self.turn)


def winner(b: Bits) -> int | None:
    has_x = any(b.x & mask == mask for mask in LINE_MASKS)
    has_o = any(b.o & mask == mask for mask in LINE_MASKS)
    if has_x and has_o:
        return b.turn
    return X if has_x else O if has_o else None


def legal_moves(b: Bits) -> tuple[Move, ...]:
    if winner(b) is not None:
        return ()
    allowed = FULL ^ (b.o if b.turn == X else b.x)
    return tuple(m for m in PATHS if allowed & (1 << m.index))


def apply(b: Bits, move: Move) -> Bits:
    if not isinstance(move, Move) or move not in PATHS or winner(b) is not None:
        raise ValueError("illegal bitboard move")
    if (b.o if b.turn == X else b.x) & (1 << move.index):
        raise ValueError("cannot select opponent cube")
    path = PATHS[move]
    remove = sum(1 << i for i in path)
    x, o = b.x & ~remove, b.o & ~remove
    for dest, src in zip(path, path[1:]):
        if b.x & (1 << src):
            x |= (1 << dest)
        elif b.o & (1 << src):
            o |= (1 << dest)
    if b.turn == X:
        x |= (1 << path[-1])
    else:
        o |= (1 << path[-1])
    return Bits(x, o, -b.turn)


def canonical(b: Bits) -> tuple[int, int, int]:
    """D4-canonical integer masks for transposition caching."""
    best = None
    for mapping in D4:
        x = o = 0
        for a, z in enumerate(mapping):
            if b.x & (1 << a):
                x |= 1 << z
            if b.o & (1 << a):
                o |= 1 << z
        candidate = (x, o)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return (b.turn, *best)
