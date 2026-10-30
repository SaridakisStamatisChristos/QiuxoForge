"""Deterministic two-player iterative-deepening alpha-beta opponent.

A move recommendation is a HEURISTIC, not a certified forced win.  For exact
finite-horizon outcomes use ReferenceSolver/BitboardSolver and checked proofs.
Every completed iteration is exact for the documented *evaluation function*
within that fixed ply horizon. Alpha-beta/TT do not change the minimax value.
"""
from __future__ import annotations

from dataclasses import dataclass
from .model import State, Move
from . import bitboard
from .bitboard import Bits, LINE_MASKS
from .symmetry import D4, transform_move

MATE = 10_000_000
WEIGHTS = (0, 2, 12, 80, 650, 5000)
INVERSE = tuple(next(j for j in range(8) if all(D4[j][D4[k][i]] == i for i in range(25))) for k in range(8))


@dataclass(frozen=True)
class Decision:
    move: Move | None
    score: int | None
    completed_depth: int
    nodes: int
    pv: tuple[Move, ...]
    aborted: bool


@dataclass(frozen=True)
class Entry:
    value: int
    flag: str
    best: Move | None


class _BudgetExceeded(Exception):
    pass


class AlphaBetaEngine:
    """Exact bounded negamax of an explicitly heuristic static evaluation.

    Caches alpha-beta bounds, with canonicalized D4 move coordinates.  A node
    budget is deterministic: interrupted iterations are discarded completely.
    """
    def __init__(self):
        self.table: dict[tuple[int, int, int, int], Entry] = {}
        self.nodes = 0
        self.max_nodes: int | None = None

    @staticmethod
    def _orientation(b: Bits) -> tuple[tuple[int, int, int], int]:
        best: tuple[int, int] | None = None
        index = 0
        for k, m in enumerate(D4):
            x = o = 0
            for old, new in enumerate(m):
                bit = 1 << old
                if b.x & bit:
                    x |= 1 << new
                if b.o & bit:
                    o |= 1 << new
            candidate = (x, o)
            if best is None or candidate < best:
                best, index = candidate, k
        assert best is not None
        return (b.turn, *best), index

    @staticmethod
    def evaluate(b: Bits) -> int:
        own, enemy = (b.x, b.o) if b.turn == 1 else (b.o, b.x)
        score = 0
        for mask in LINE_MASKS:
            a = (own & mask).bit_count()
            z = (enemy & mask).bit_count()
            if not z:
                score += WEIGHTS[a]
            if not a:
                score -= WEIGHTS[z]
        return score

    def _node(self) -> None:
        self.nodes += 1
        if self.max_nodes is not None and self.nodes > self.max_nodes:
            raise _BudgetExceeded

    def _order(self, b: Bits, moves: tuple[Move, ...], preferred: Move | None) -> list[Move]:
        """Deterministic tactical ordering, independent of transposition key."""
        ranked = []
        for move in moves:
            child = bitboard.apply(b, move)
            win = bitboard.winner(child)
            immediate = 1 if win == b.turn else -1 if win is not None else 0
            ranked.append((-int(move == preferred), -immediate, self.evaluate(child), move.index, move.edge, move))
        ranked.sort(key=lambda z: z[:-1])
        return [x[-1] for x in ranked]

    def _search(self, b: Bits, depth: int, alpha: int, beta: int) -> tuple[int, Move | None]:
        self._node()
        w = bitboard.winner(b)
        if w is not None:
            return (MATE + depth if w == b.turn else -MATE - depth), None
        if depth == 0:
            return self.evaluate(b), None
        moves = bitboard.legal_moves(b)
        if not moves:
            # No declared blocked-state outcome: neutral heuristic score.
            return self.evaluate(b), None
        key0, transform = self._orientation(b)
        key = (*key0, depth)
        start_alpha, start_beta = alpha, beta
        entry = self.table.get(key)
        preferred = transform_move(entry.best, INVERSE[transform]) if entry and entry.best else None
        if entry:
            if entry.flag == "EXACT":
                return entry.value, preferred
            if entry.flag == "LOWER":
                alpha = max(alpha, entry.value)
            if entry.flag == "UPPER":
                beta = min(beta, entry.value)
            if alpha >= beta:
                return entry.value, preferred
        best_move = None
        best_val = -2 * MATE
        for move in self._order(b, moves, preferred):
            v, _ = self._search(bitboard.apply(b, move), depth-1, -beta, -alpha)
            v = -v
            if v > best_val:
                best_val, best_move = v, move
            alpha = max(alpha, v)
            if alpha >= beta:
                break
        flag = "UPPER" if best_val <= start_alpha else "LOWER" if best_val >= start_beta else "EXACT"
        self.table[key] = Entry(best_val, flag, transform_move(best_move, transform))
        return best_val, best_move

    def recommend(self, state: State | Bits, *, depth: int = 3, max_nodes: int | None = None) -> Decision:
        if type(depth) is not int or depth < 1:
            raise ValueError("depth must be positive integer")
        if max_nodes is not None and (type(max_nodes) is not int or max_nodes <= 0):
            raise ValueError("max_nodes must be positive integer or None")
        b = Bits.from_state(state) if isinstance(state, State) else state
        if not isinstance(b, Bits):
            raise TypeError("expected State or Bits")
        if bitboard.winner(b) is not None or not bitboard.legal_moves(b):
            return Decision(None, None, 0, 0, (), False)
        self.nodes = 0
        self.max_nodes = max_nodes
        self.table.clear()
        last: tuple[int, Move] | None = None
        completed = 0
        aborted = False
        for d in range(1, depth+1):
            try:
                value, move = self._search(b, d, -2*MATE, 2*MATE)
            except _BudgetExceeded:
                aborted = True
                break
            if move is None:
                raise AssertionError("nonterminal search has no move")
            last, completed = (value, move), d
        if last is None:
            return Decision(None, None, 0, self.nodes, (), True)
        # Extract PV only through certified EXACT transpositions. Re-evaluate
        # no speculative alpha-beta cut branches while constructing the path.
        path: list[Move] = [last[1]]
        if completed > 1:
            cur = bitboard.apply(b, last[1])
            for d in range(completed - 1, 0, -1):
                key, transform = self._orientation(cur)
                entry = self.table.get((*key, d))
                if not entry or entry.flag != "EXACT" or entry.best is None:
                    break
                m = transform_move(entry.best, INVERSE[transform])
                if m not in bitboard.legal_moves(cur):
                    raise AssertionError("PV has illegal transposed move")
                path.append(m)
                cur = bitboard.apply(cur, m)
        return Decision(last[1], last[0], completed, self.nodes, tuple(path), aborted)
