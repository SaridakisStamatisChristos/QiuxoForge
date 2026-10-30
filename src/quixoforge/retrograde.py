"""Exact loopy finite-game analysis (exhaustive graph, no search cutoff).

A WIN forces an eventual win, a LOSS is an eventual forced loss, and a
NONFORCED position is neither: with perfect play, a player can avoid losing
but no player can force a win. This is called 'draw' in standard game-solving
conventions, but Quixo's printed rules do not prescribe a repetition draw.

The solver is game-generic: states and actions are hashable; the game supplies
legal_moves, apply, winner and turn as in solver.FiniteGame. Every reachable
successor must be explicitly enumerated. An exceeded max_states RAISES; it
never silently classifies truncated nodes as NONFORCED.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from heapq import heappop, heappush
from types import MappingProxyType
from typing import Generic, Hashable, Mapping, TypeVar

from .solver import FiniteGame

S = TypeVar('S', bound=Hashable)
M = TypeVar('M')


class Outcome(str, Enum):
    WIN = 'WIN'
    LOSS = 'LOSS'
    NONFORCED = 'NONFORCED'


@dataclass(frozen=True)
class Retrograde(Generic[S, M]):
    root: S
    outcomes: Mapping[S, Outcome]
    remoteness: Mapping[S, int]
    successors: Mapping[S, tuple[S, ...]]
    edge_count: int

    def outcome(self, state: S) -> Outcome:
        return self.outcomes[state]

    def best_successor(self, state: S) -> S | None:
        """Optimal successor; for wins minimizes win distance, for losses delays loss.

        For NONFORCED, returns a successor which is not a forced WIN for the
        opposing player. Caller must map the selected successor to its action.
        """
        children = self.successors[state]
        if not children:
            return None
        kind = self.outcomes[state]
        if kind == Outcome.WIN:
            return min((c for c in children if self.outcomes[c] == Outcome.LOSS),
                       key=lambda c: self.remoteness[c])
        if kind == Outcome.LOSS:
            return max(children, key=lambda c: self.remoteness[c])
        return next(c for c in children if self.outcomes[c] == Outcome.NONFORCED)


def solve(game: FiniteGame, root: S, *, max_states: int = 100_000) -> Retrograde[S, M]:
    if type(max_states) is not int or max_states < 1:
        raise ValueError('max_states must be a positive integer')
    states = {root}
    pending = deque([root])
    successors: dict[S, tuple[S, ...]] = {}
    predecessors: dict[S, list[S]] = {}
    remaining: dict[S, int] = {}
    winner: dict[S, int | None] = {}
    edge_count = 0
    while pending:
        state = pending.popleft()
        w = game.winner(state)
        winner[state] = w
        if w is not None:
            moves = ()
        else:
            moves = game.legal_moves(state)
            if not moves:
                raise ValueError('nonterminal position with no legal moves: no adjudication specified')
        children = []
        for move in moves:
            child = game.apply(state, move)
            if child not in states:
                if len(states) >= max_states:
                    raise ValueError('max_states exceeded; graph is incomplete')
                states.add(child)
                pending.append(child)
            children.append(child)
            predecessors.setdefault(child, []).append(state)
        successors[state] = tuple(children)
        remaining[state] = len(children)
        edge_count += len(children)

    # Remoteness-prioritized retrograde propagation: first discovered LOSS
    # successor gives a minimum winning remoteness, whereas LOSS waits for
    # the largest remoteness of all forced-WIN children.
    values: dict[S, Outcome] = {}
    distance: dict[S, int] = {}
    max_winning_child: dict[S, int] = {}
    heap: list[tuple[int, int, S]] = []
    serial = 0
    for state, w in winner.items():
        if w is not None:
            values[state] = Outcome.WIN if w == game.turn(state) else Outcome.LOSS
            distance[state] = 0
            heappush(heap, (0, serial, state))
            serial += 1
    while heap:
        d, _, child = heappop(heap)
        for parent in predecessors.get(child, ()):
            if parent in values:
                continue
            if values[child] == Outcome.LOSS:
                values[parent] = Outcome.WIN
                distance[parent] = d + 1
                heappush(heap, (d+1, serial, parent))
                serial += 1
            else:
                remaining[parent] -= 1
                max_winning_child[parent] = max(d, max_winning_child.get(parent, 0))
                if not remaining[parent]:
                    values[parent] = Outcome.LOSS
                    distance[parent] = max_winning_child[parent] + 1
                    heappush(heap, (distance[parent], serial, parent))
                    serial += 1
    for state in states:
        if state not in values:
            values[state] = Outcome.NONFORCED
    return Retrograde(root, MappingProxyType(values), MappingProxyType(distance),
                     MappingProxyType(successors), edge_count)


def verify(game: FiniteGame, result: Retrograde) -> None:
    """Independent algebraic verification of *every* state and graph edge.

    Checks graph closure, transition reconstruction, terminal outcomes, each
    winner/loser remoteness equation, and the NONFORCED closed subgame. Does
    not call solve; catches incomplete graphs and fabricated classifications.
    """
    graph, outcomes, distance = result.successors, result.outcomes, result.remoteness
    if set(graph) != set(outcomes) or sum(map(len, graph.values())) != result.edge_count:
        raise ValueError('graph not closed or edge-count mismatch')
    for state, children in graph.items():
        w = game.winner(state)
        expected = () if w is not None else tuple(game.apply(state, m) for m in game.legal_moves(state))
        if children != expected:
            raise ValueError('graph transition or terminal mismatch')
        kind = outcomes[state]
        if w is not None:
            if kind != (Outcome.WIN if w == game.turn(state) else Outcome.LOSS) or distance.get(state) != 0:
                raise ValueError('terminal label mismatch')
        elif not children:
            raise ValueError('unadjudicated blocked state')
        elif kind == Outcome.WIN:
            choices = [distance[c] for c in children if outcomes[c] == Outcome.LOSS]
            if not choices or distance.get(state) != 1 + min(choices):
                raise ValueError('incorrect WIN remoteness')
        elif kind == Outcome.LOSS:
            if any(outcomes[c] != Outcome.WIN for c in children) or distance.get(state) != 1 + max(distance[c] for c in children):
                raise ValueError('incorrect LOSS remoteness')
        elif kind == Outcome.NONFORCED:
            if state in distance or any(outcomes[c] == Outcome.LOSS for c in children) or all(outcomes[c] == Outcome.WIN for c in children):
                raise ValueError('incorrect NONFORCED subgame')
        else:
            raise ValueError('unknown outcome')
