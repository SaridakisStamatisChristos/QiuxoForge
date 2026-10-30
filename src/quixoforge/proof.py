"""Inductively checkable finite-horizon AND/OR tactical proof certificates.

A WIN node supplies ONE move whose child is LOSS. A LOSS node supplies EVERY
legal move, each with a WIN child. Leaves are actual terminal outcomes.
UNKNOWN positions cannot be certified. A checker does not trust the solver,
transposition tables, symmetry transform, or purported result labels.
"""
from __future__ import annotations
from .model import State, Move
from .reference import legal_moves, apply, winner
from .solver import ReferenceSolver, Result


def produce(state: State, depth: int, solver: ReferenceSolver | None = None) -> dict:
    if solver is None:
        solver = ReferenceSolver()
    value = solver.solve(state, depth)
    if value == Result.UNKNOWN:
        raise ValueError("no bounded proof for UNKNOWN")
    w = winner(state)
    if w is not None:
        return {"outcome": value.value, "terminal": True}
    if depth <= 0:
        raise AssertionError("nonterminal leaf cannot be a proven outcome")
    legal = legal_moves(state)
    if value == Result.WIN:
        for m in legal:
            child = apply(state, m)
            if solver.solve(child, depth-1) == Result.LOSS:
                return {"outcome": "WIN", "move": str(m), "child": produce(child, depth-1, solver)}
        raise AssertionError("unwitnessed WIN")
    return {"outcome": "LOSS", "replies": {
        str(m): produce(apply(state, m), depth-1, solver) for m in legal
    }}


def verify(state: State, depth: int, proof: dict) -> Result:
    """Raise ValueError for omitted defenses, illegal moves or false leaves."""
    if type(proof) is not dict or proof.get("outcome") not in ("WIN", "LOSS"):
        raise ValueError("invalid proof node")
    expected = Result(proof["outcome"])
    w = winner(state)
    if w is not None:
        if proof != {"outcome": expected.value, "terminal": True}:
            raise ValueError("terminal certificate malformed")
        if (w == state.turn) != (expected == Result.WIN):
            raise ValueError("false terminal outcome")
        return expected
    if depth <= 0:
        raise ValueError("nonterminal at depth limit")
    moves = legal_moves(state)
    if not moves:
        raise ValueError("blocked position has no declared winner")
    if expected == Result.WIN:
        if set(proof) != {"outcome", "move", "child"}:
            raise ValueError("malformed existential node")
        try:
            m = Move.parse(proof["move"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("invalid proof move") from exc
        if m not in moves or verify(apply(state, m), depth-1, proof["child"]) != Result.LOSS:
            raise ValueError("invalid winning witness")
    else:
        if set(proof) != {"outcome", "replies"} or not isinstance(proof["replies"], dict):
            raise ValueError("malformed universal node")
        replies = proof["replies"]
        if set(replies) != {str(m) for m in moves}:
            raise ValueError("missing or unexpected opponent defense")
        for m in moves:
            if verify(apply(state, m), depth-1, replies[str(m)]) != Result.WIN:
                raise ValueError("false opponent defense")
    return expected
