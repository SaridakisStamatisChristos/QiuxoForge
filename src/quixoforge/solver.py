"""Two independent exact *bounded* minimax searches.

WIN = player-to-move has a forced victory within the remaining ply budget.
LOSS = every legal move lets opponent force victory within that budget.
UNKNOWN = neither proposition was proved. No rule for repetition or blocked
positions is invented. Thus UNKNOWN never means a game-theoretic draw.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, Hashable
from .model import State, Move
from . import reference
from .bitboard import Bits
from . import bitboard
from .symmetry import canonical as ref_canonical


class Result(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    UNKNOWN = "UNKNOWN"


T = TypeVar("T")
M = TypeVar("M")


class FiniteGame(Protocol[T, M]):
    """Core interface intended for future abstract strategy games."""
    def legal_moves(self, s: T) -> tuple[M, ...]: ...
    def apply(self, s: T, move: M) -> T: ...
    def winner(self, s: T) -> int | None: ...
    def turn(self, s: T) -> int: ...
    def cache_key(self, s: T) -> Hashable: ...


class ReferenceGame:
    def legal_moves(self, s: State) -> tuple[Move, ...]: return reference.legal_moves(s)
    def apply(self, s: State, move: Move) -> State: return reference.apply(s, move)
    def winner(self, s: State) -> int | None: return reference.winner(s)
    def turn(self, s: State) -> int: return s.turn
    def cache_key(self, s: State) -> Hashable: return s  # no symmetry reduction in oracle


@dataclass
class Stats:
    nodes: int = 0
    cache_hits: int = 0
    entries: int = 0


class ReferenceSolver:
    """Generic non-symmetry oracle, independently transitioning Python tuples."""
    def __init__(self, game: FiniteGame = None):
        self.game = game if game is not None else ReferenceGame()
        self.table: dict[tuple[Hashable, int], Result] = {}
        self.stats = Stats()

    def solve(self, s: State, depth: int) -> Result:
        if type(depth) is not int or depth < 0:
            raise ValueError("depth must be a nonnegative integer")
        k = (self.game.cache_key(s), depth)
        if k in self.table:
            self.stats.cache_hits += 1
            return self.table[k]
        self.stats.nodes += 1
        win = self.game.winner(s)
        if win is not None:
            out = Result.WIN if win == self.game.turn(s) else Result.LOSS
        elif depth == 0:
            out = Result.UNKNOWN
        else:
            moves = self.game.legal_moves(s)
            # Unspecified blocked state is neither a win nor a loss.
            out = Result.UNKNOWN
            if moves:
                all_opponent_wins = True
                for move in moves:
                    child = self.solve(self.game.apply(s, move), depth-1)
                    if child == Result.LOSS:
                        out = Result.WIN
                        break
                    if child != Result.WIN:
                        all_opponent_wins = False
                else:
                    if all_opponent_wins:
                        out = Result.LOSS
        self.table[k] = out
        self.stats.entries = len(self.table)
        return out


class BitboardSolver:
    """Bitboard transitions, D4 canonical memo keys and early-win pruning."""
    def __init__(self):
        self.table: dict[tuple[int, int, int, int], Result] = {}
        self.stats = Stats()

    def solve(self, state: State | Bits, depth: int) -> Result:
        if type(depth) is not int or depth < 0:
            raise ValueError("depth must be a nonnegative integer")
        b = Bits.from_state(state) if isinstance(state, State) else state
        if not isinstance(b, Bits):
            raise TypeError("expected State or Bits")
        return self._search(b, depth)

    def _search(self, b: Bits, depth: int) -> Result:
        key = (*bitboard.canonical(b), depth)
        if key in self.table:
            self.stats.cache_hits += 1
            return self.table[key]
        self.stats.nodes += 1
        terminal = bitboard.winner(b)
        if terminal is not None:
            outcome = Result.WIN if terminal == b.turn else Result.LOSS
        elif depth == 0:
            outcome = Result.UNKNOWN
        else:
            moves = bitboard.legal_moves(b)
            outcome = Result.UNKNOWN
            if moves:
                all_win = True
                for move in moves:
                    v = self._search(bitboard.apply(b, move), depth-1)
                    if v == Result.LOSS:
                        outcome = Result.WIN
                        break
                    if v != Result.WIN:
                        all_win = False
                else:
                    if all_win:
                        outcome = Result.LOSS
        self.table[key] = outcome
        self.stats.entries = len(self.table)
        return outcome


def winning_moves(state: State, depth: int, solver: ReferenceSolver | BitboardSolver) -> tuple[Move, ...]:
    if depth <= 0:
        return ()
    return tuple(m for m in reference.legal_moves(state)
                 if solver.solve(reference.apply(state, m), depth-1) == Result.LOSS)
