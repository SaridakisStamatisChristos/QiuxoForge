"""Replayable tactical puzzles with two independent search-oracle checks."""
from __future__ import annotations
from dataclasses import dataclass
from .model import State, Move, replay
from .reference import legal_moves, apply, winner
from .solver import ReferenceSolver, BitboardSolver, Result, winning_moves
from .proof import produce, verify


@dataclass(frozen=True)
class Puzzle:
    history: tuple[Move, ...]
    bound: int
    start: int = 1

    def state(self) -> State:
        return replay(self.history, self.start)


@dataclass(frozen=True)
class Audit:
    bound: int
    minimal_bound: int
    solutions: tuple[Move, ...]
    difficulty: str
    reference_nodes: int
    bitboard_nodes: int


def audit(puzzle: Puzzle, *, require_unique: bool = False) -> Audit:
    """Check exact bounded claim from legal replay and independent transitions.

    A tactical difficulty tier denotes *minimum proven forcing horizon* only.
    It is NOT a psychometric or human skill-difficulty score.
    """
    s = puzzle.state()
    if type(puzzle.bound) is not int or not 1 <= puzzle.bound <= 9:
        raise ValueError("puzzle bound must be integer 1..9")
    if winner(s) is not None:
        raise ValueError("already-terminal state is not a tactical puzzle")
    ref = ReferenceSolver()
    fast = BitboardSolver()
    if ref.solve(s, puzzle.bound) != Result.WIN or fast.solve(s, puzzle.bound) != Result.WIN:
        raise ValueError("forced win not independently proved")
    ref_solutions = winning_moves(s, puzzle.bound, ref)
    fast_solutions = winning_moves(s, puzzle.bound, fast)
    if not ref_solutions or set(ref_solutions) != set(fast_solutions):
        raise ValueError("solver disagreement on complete solution set")
    if require_unique and len(ref_solutions) != 1:
        raise ValueError("puzzle does not have a unique winning first move")
    horizon_values = [(d, ref.solve(s, d), fast.solve(s, d)) for d in range(1, puzzle.bound+1)]
    if any(a != b for _, a, b in horizon_values):
        raise ValueError("independent solvers disagree about shorter forcing horizons")
    first_bound = next((d for d,a,b in horizon_values if a == Result.WIN), None)
    if first_bound is None:
        raise AssertionError("minimal horizon not found")
    # Force independent recursive certificate verification, rather than trusting
    # the same value cache that discovered the solution.
    witness = produce(s, first_bound, ref)
    if verify(s, first_bound, witness) != Result.WIN:
        raise AssertionError("proof verification failed")
    tier = "immediate" if first_bound == 1 else "short-forcing" if first_bound <= 3 else "deep-forcing"
    return Audit(puzzle.bound, first_bound, ref_solutions, tier, ref.stats.nodes, fast.stats.nodes)
