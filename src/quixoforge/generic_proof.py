"""Game-agnostic finite-horizon AND/OR certificate producer and verifier.

This checker does not call a solver, cache, symmetry routine, or trust a
claimed result: it recursively checks the game's rules, all existential and
universal moves, and terminal outcomes.  Game adapters remain the trusted
semantic boundary, so using independent adapters is recommended.
"""
from __future__ import annotations
from typing import Hashable, TypeVar
from .solver import FiniteGame, ReferenceSolver, Result

S = TypeVar("S")
M = TypeVar("M")


def _actions(game: FiniteGame, state) -> dict[str, object]:
    moves = game.legal_moves(state)
    labels = {str(m): m for m in moves}
    if len(moves) != len(labels):
        raise ValueError("game action strings must be unique to certify")
    return labels


def produce(game: FiniteGame, state, depth: int, solver: ReferenceSolver | None = None) -> dict:
    """Produce a complete WIN/LOSS proof tree or reject UNKNOWN positions."""
    if type(depth) is not int or depth < 0:
        raise ValueError("depth must be nonnegative int")
    if solver is None:
        solver = ReferenceSolver(game)
    value = solver.solve(state, depth)
    if value == Result.UNKNOWN:
        raise ValueError("cannot certify unknown finite-horizon outcome")
    winner = game.winner(state)
    if winner is not None:
        return {"outcome": value.value, "terminal": True}
    if depth == 0:
        raise AssertionError("a nonterminal certificate requires positive depth")
    moves = _actions(game, state)
    if not moves:
        raise ValueError("blocked unadjudicated position")
    if value == Result.WIN:
        for name, move in moves.items():
            child = game.apply(state, move)
            if solver.solve(child, depth-1) == Result.LOSS:
                return {"outcome": "WIN", "move": name,
                        "child": produce(game, child, depth-1, solver)}
        raise AssertionError("solver supplied WIN without a witness")
    return {"outcome": "LOSS", "replies": {
        name: produce(game, game.apply(state, move), depth-1, solver)
        for name, move in moves.items()}}


def verify(game: FiniteGame, state, depth: int, certificate: dict) -> Result:
    """Recursively check proof; raises ValueError on missing/illegal defenses."""
    if type(depth) is not int or depth < 0:
        raise ValueError("depth must be nonnegative int")
    if type(certificate) is not dict or certificate.get("outcome") not in ("WIN", "LOSS"):
        raise ValueError("invalid proof")
    value = Result(certificate["outcome"])
    w = game.winner(state)
    if w is not None:
        if certificate != {"outcome": value.value, "terminal": True}:
            raise ValueError("malformed terminal proof")
        if (w == game.turn(state)) != (value == Result.WIN):
            raise ValueError("false terminal proof")
        return value
    if depth == 0:
        raise ValueError("nonterminal leaf at depth zero")
    moves = _actions(game, state)
    if not moves:
        raise ValueError("no declared terminal on blocked state")
    if value == Result.WIN:
        if set(certificate) != {"outcome", "move", "child"}:
            raise ValueError("malformed existential node")
        label = certificate["move"]
        if not isinstance(label, str) or label not in moves:
            raise ValueError("unavailable winning move")
        if verify(game, game.apply(state,moves[label]), depth-1, certificate["child"]) != Result.LOSS:
            raise ValueError("false winning witness")
    else:
        if set(certificate) != {"outcome", "replies"} or type(certificate["replies"]) is not dict:
            raise ValueError("malformed universal node")
        replies = certificate["replies"]
        if set(replies) != set(moves):
            raise ValueError("missing or extra defense")
        for name, move in moves.items():
            if verify(game, game.apply(state,move), depth-1, replies[name]) != Result.WIN:
                raise ValueError("false defense")
    return value
