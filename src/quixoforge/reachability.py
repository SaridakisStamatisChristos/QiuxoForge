"""Exact small-occupancy reachability, with shortest constructive witnesses.

For each fixed initial side and occupancy bound K, BFS enumerates the complete
reachable induced subgraph of positions with <=K marked cubes. This restriction
is *exact* for any target with <=K marked cubes because a legal Quixo move
never removes a mark, so no path to such a target can pass through a state
with >K marks. This does NOT decide reachability for targets outside the
indexed domain; nor does it imply anything about unrestricted optimal play.

This intentionally uses reference rules rather than relying on bitboard solver
transpositions. The finite bound K<=3 keeps the index tractable in pure Python.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .model import Move, State, X, O, initial, replay
from . import reference


def occupancy(state: State) -> int:
    """Number of nonblank cells; exactly nondecreasing under legal moves."""
    if not isinstance(state, State):
        raise TypeError("expected State")
    return sum(v != 0 for v in state.cells)


@dataclass(frozen=True)
class ReachabilityIndex:
    """Complete reachability certificate for the *declared* occupancy scope.

    A target outside the bound raises ValueError, never returning False. For
    targets inside, a negative result is exact (assuming the specified start).
    Every positive result has a shortest legal-history witness, in plies.
    """
    start: int
    max_stones: int
    _parents: Mapping[State, tuple[State, Move] | None]
    examined_edges: int

    @classmethod
    def build(cls, max_stones: int = 2, *, start: int = X) -> "ReachabilityIndex":
        if type(max_stones) is not int or not 0 <= max_stones <= 3:
            raise ValueError("exact reachability index supports occupancy bounds 0..3")
        root = initial(start)
        parents: dict[State, tuple[State, Move] | None] = {root: None}
        queue = deque([root])
        examined_edges = 0
        while queue:
            position = queue.popleft()
            total = occupancy(position)
            for move in reference.legal_moves(position):
                # Blank selection creates one new mark. At the cap it cannot
                # lead back inside the indexed domain, so skip before the
                # expensive shift. Still count the legal candidate edge.
                examined_edges += 1
                if total == max_stones and position.cells[move.index] == 0:
                    continue
                child = reference.apply(position, move)
                if occupancy(child) <= max_stones and child not in parents:
                    parents[child] = (position, move)
                    queue.append(child)
        return cls(start, max_stones, MappingProxyType(parents), examined_edges)

    @property
    def state_count(self) -> int:
        return len(self._parents)

    def _check_domain(self, target: State) -> None:
        if not isinstance(target, State):
            raise TypeError("target must be State")
        if occupancy(target) > self.max_stones:
            raise ValueError("target outside the proved occupancy domain")

    def is_reachable(self, target: State) -> bool:
        """Exact yes/no within the indexed domain, not a heuristic."""
        self._check_domain(target)
        return target in self._parents

    def witness(self, target: State) -> tuple[Move, ...] | None:
        """Return a shortest complete legal history; None proves unreachable."""
        self._check_domain(target)
        if target not in self._parents:
            return None
        steps: list[Move] = []
        cursor = target
        while (predecessor := self._parents[cursor]) is not None:
            parent, move = predecessor
            steps.append(move)
            cursor = parent
        steps.reverse()
        proof = tuple(steps)
        if replay(proof, self.start) != target:
            raise AssertionError("reachability witness failed independent replay")
        return proof
