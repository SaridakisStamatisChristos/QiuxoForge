"""Deterministic generation of *fully certified* two-player tactical puzzles.

Candidates without a complete independent finite-horizon proof are rejected.
Every emitted document can be validated by verify_examples.check.  Sampling
never justifies completeness or human-difficulty claims.
"""
from __future__ import annotations
import random
from .model import Move, replay, initial
from . import reference
from .puzzles import Puzzle, audit
from .solver import ReferenceSolver, Result
from .proof import produce, verify
from .symmetry import canonical


def certify(history: tuple[Move, ...], bound: int, *, unique: bool = True) -> dict:
    """Return schema-1 certificate ONLY when all correctness gates succeed."""
    puzzle = Puzzle(history, bound)
    report = audit(puzzle, require_unique=unique)
    position = puzzle.state()
    proof = produce(position, bound)
    if verify(position, bound, proof) != Result.WIN:
        raise AssertionError("unverified puzzle emitted")
    return {"schema": 1, "history": [str(m) for m in history],
            "depth": bound, "unique": unique,
            "solutions": [str(m) for m in report.solutions],
            "minimal_bound": report.minimal_bound,
            "difficulty": report.difficulty,
            "proof": proof}


def generate(*, seed: int, bound: int = 1, attempts: int = 500,
             min_plies: int = 8, max_plies: int = 32, unique: bool = True) -> dict:
    """Find a proved puzzle or raise LookupError; never emit a weak candidate.

    Uses a deterministic seeded random walk with an independent exact auditor.
    A failed bounded search says nothing about existence of other puzzles.
    """
    if any(type(v) is not int for v in (seed,bound,attempts,min_plies,max_plies)):
        raise ValueError("generator parameters must be integers")
    if not 1 <= bound <= 9 or attempts <= 0 or min_plies < 0 or max_plies < min_plies:
        raise ValueError("invalid generator limits")
    rng = random.Random(seed)
    visited: set[tuple] = set()
    for _ in range(attempts):
        s = initial()
        history: list[Move] = []
        for ply in range(max_plies+1):
            if reference.winner(s) is not None:
                break
            if ply >= min_plies:
                key = canonical(s)
                if key not in visited:
                    visited.add(key)
                    if ReferenceSolver().solve(s, bound) == Result.WIN:
                        try:
                            doc = certify(tuple(history), bound, unique=unique)
                        except ValueError:
                            pass
                        else:
                            doc["generation"] = {"seed": seed, "attempts": attempts,
                                                 "min_plies": min_plies, "max_plies": max_plies,
                                                 "uniqueness_required": unique}
                            return doc
            if ply == max_plies:
                break
            moves = reference.legal_moves(s)
            if not moves:
                break
            m = rng.choice(moves)
            s = reference.apply(s, m)
            history.append(m)
    raise LookupError("no fully certified puzzle found in the specified deterministic search")
