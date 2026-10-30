"""Independent variable-sized two-player Quixo rule implementations.

Reference uses copied cells and explicit shifts. Mask model uses bitwise
occupancy and precomputed paths. Sizes 2..5 use the same *rules* as Quixo,
but 2..4 are research variants, not the official 5x5 board.

The two implementations never delegate move generation or application to one
another or to the fixed 5x5 code. They share only the immutable Move type.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import Move, X, O


@dataclass(frozen=True)
class VariantState:
    cells: tuple[int, ...]
    turn: int = X
    size: int = 3

    def __post_init__(self) -> None:
        if type(self.size) is not int or not 2 <= self.size <= 5:
            raise ValueError('size must be an integer between 2 and 5')
        if type(self.cells) is not tuple or len(self.cells) != self.size ** 2:
            raise ValueError('invalid variant board length')
        if any(type(v) is not int or v not in (0, X, O) for v in self.cells):
            raise ValueError('invalid variant board value')
        if type(self.turn) is not int or self.turn not in (X, O):
            raise ValueError('invalid side to move')


@dataclass(frozen=True)
class VariantBits:
    x: int
    o: int
    turn: int = X
    size: int = 3

    def __post_init__(self) -> None:
        if type(self.size) is not int or not 2 <= self.size <= 5:
            raise ValueError('invalid size')
        if type(self.x) is not int or type(self.o) is not int or self.x < 0 or self.o < 0:
            raise ValueError('invalid occupancy masks')
        if (self.x | self.o) >> (self.size ** 2) or (self.x & self.o):
            raise ValueError('overlapping or out-of-board masks')
        if type(self.turn) is not int or self.turn not in (X, O):
            raise ValueError('invalid side to move')

    @classmethod
    def from_state(cls, state: VariantState) -> 'VariantBits':
        return cls(sum(1 << i for i, v in enumerate(state.cells) if v == X),
                   sum(1 << i for i, v in enumerate(state.cells) if v == O),
                   state.turn, state.size)

    def state(self) -> VariantState:
        return VariantState(tuple(X if self.x & (1 << i) else O if self.o & (1 << i) else 0
                                  for i in range(self.size**2)), self.turn, self.size)


def initial(size: int = 3, *, start: int = X) -> VariantState:
    if type(size) is not int or not 2 <= size <= 5:
        raise ValueError('size must be 2..5')
    return VariantState((0,) * (size ** 2), start, size)


class VariantReference:
    """Reference cell-array transitions, independent of 5x5 and bitboard code."""
    def __init__(self, size: int = 3):
        initial(size)
        self.size = size

    def _check(self, state: VariantState) -> None:
        if not isinstance(state, VariantState) or state.size != self.size:
            raise ValueError('state belongs to a different variant')

    def winner(self, state: VariantState) -> int | None:
        self._check(state)
        n, b = self.size, state.cells
        lines = []
        for r in range(n):
            lines.append(tuple(b[n*r+c] for c in range(n)))
        for c in range(n):
            lines.append(tuple(b[n*r+c] for r in range(n)))
        lines.append(tuple(b[(n+1)*k] for k in range(n)))
        lines.append(tuple(b[(n-1)*(k+1)] for k in range(n)))
        x = any(a[0] == X and all(v == X for v in a) for a in lines)
        o = any(a[0] == O and all(v == O for v in a) for a in lines)
        return state.turn if x and o else X if x else O if o else None

    def legal_moves(self, state: VariantState) -> tuple[Move, ...]:
        self._check(state)
        if self.winner(state) is not None:
            return ()
        n = self.size
        result = []
        for index, mark in enumerate(state.cells):
            r, c = divmod(index, n)
            if r not in (0, n-1) and c not in (0, n-1):
                continue
            if mark not in (0, state.turn):
                continue
            if c: result.append(Move(index, 'L'))
            if c < n-1: result.append(Move(index, 'R'))
            if r: result.append(Move(index, 'U'))
            if r < n-1: result.append(Move(index, 'D'))
        return tuple(result)

    def apply(self, state: VariantState, move: Move) -> VariantState:
        if not isinstance(move, Move) or move not in self.legal_moves(state):
            raise ValueError('illegal variant move')
        n = self.size
        r, c = divmod(move.index, n)
        step = {'L': -1, 'R': 1, 'U': -n, 'D': n}[move.edge]
        length = c if move.edge == 'L' else n-1-c if move.edge == 'R' else r if move.edge == 'U' else n-1-r
        path = [move.index + j*step for j in range(length+1)]
        cells = list(state.cells)
        for dest, src in zip(path, path[1:]):
            cells[dest] = cells[src]
        cells[path[-1]] = state.turn
        return VariantState(tuple(cells), -state.turn, n)

    def turn(self, state: VariantState) -> int:
        self._check(state)
        return state.turn

    def cache_key(self, state: VariantState):
        self._check(state)
        return state


class VariantBitboard:
    """Independent mask shifts and bitwise victory checks."""
    def __init__(self, size: int = 3):
        initial(size)
        self.size = size
        n = size
        self.lines = tuple(
            [sum(1 << (r*n+c) for c in range(n)) for r in range(n)] +
            [sum(1 << (r*n+c) for r in range(n)) for c in range(n)] +
            [sum(1 << (r*(n+1)) for r in range(n)),
             sum(1 << (n-1 + r*(n-1)) for r in range(n))]
        )
        paths: dict[Move, tuple[int, ...]] = {}
        for index in range(n*n):
            r, c = divmod(index, n)
            if r not in (0,n-1) and c not in (0,n-1): continue
            for direction, dr, dc in (('L', 0, -1), ('R',0,1), ('U',-1,0), ('D',1,0)):
                line = [index]
                rr, cc = r+dr, c+dc
                while 0 <= rr < n and 0 <= cc < n:
                    line.append(rr*n+cc)
                    rr += dr
                    cc += dc
                if len(line)>1:
                    paths[Move(index,direction)] = tuple(line)
        self.paths = paths

    def _check(self, state: VariantBits):
        if not isinstance(state, VariantBits) or state.size != self.size:
            raise ValueError('bitboard belongs to different variant')

    def winner(self, state: VariantBits) -> int | None:
        self._check(state)
        has_x = any(state.x & mask == mask for mask in self.lines)
        has_o = any(state.o & mask == mask for mask in self.lines)
        return state.turn if has_x and has_o else X if has_x else O if has_o else None

    def legal_moves(self, state: VariantBits) -> tuple[Move, ...]:
        self._check(state)
        if self.winner(state) is not None:
            return ()
        opponent = state.o if state.turn == X else state.x
        return tuple(move for move in self.paths if not (opponent & (1 << move.index)))

    def apply(self, state: VariantBits, move: Move) -> VariantBits:
        self._check(state)
        if move not in self.legal_moves(state):
            raise ValueError('illegal variant bitboard move')
        path = self.paths[move]
        clear = sum(1 << i for i in path)
        new_x, new_o = state.x & ~clear, state.o & ~clear
        for dst, src in zip(path, path[1:]):
            if state.x & (1 << src): new_x |= 1 << dst
            if state.o & (1 << src): new_o |= 1 << dst
        if state.turn == X: new_x |= 1 << path[-1]
        else: new_o |= 1 << path[-1]
        return VariantBits(new_x, new_o, -state.turn, self.size)

    def turn(self, state: VariantBits) -> int:
        self._check(state)
        return state.turn

    def cache_key(self, state: VariantBits):
        self._check(state)
        return state
