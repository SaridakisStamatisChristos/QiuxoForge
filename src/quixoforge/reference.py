"""Clarity-first Quixo reference: list shifts, direct board scans, no bitboards.

Two-player rules: an edge cube must be blank or own; it is reinserted at a
*different* extremity of its row/column. The old values slide toward the hole.
"""
from __future__ import annotations
from .model import State, Move, X, O


def winner(state: State) -> int | None:
    lines: set[int] = set()
    b = state.cells
    for r in range(5):
        row = b[5*r:5*r+5]
        if row[0] and all(v == row[0] for v in row):
            lines.add(row[0])
    for c in range(5):
        col = [b[5*r+c] for r in range(5)]
        if col[0] and all(v == col[0] for v in col):
            lines.add(col[0])
    for col in ([b[6*i] for i in range(5)], [b[4+4*i] for i in range(5)]):
        if col[0] and all(v == col[0] for v in col):
            lines.add(col[0])
    if len(lines) == 2:
        # Last mover was -state.turn: if both lines were made, that mover loses.
        return state.turn
    return next(iter(lines)) if lines else None


def legal_moves(s: State) -> tuple[Move, ...]:
    if winner(s) is not None:
        return ()
    moves: list[Move] = []
    for r in range(5):
        for c in range(5):
            if r not in (0, 4) and c not in (0, 4):
                continue
            pos = r*5+c
            if s.cells[pos] not in (0, s.turn):
                continue
            # One may push from any other end of that row or column.
            if c > 0:
                moves.append(Move(pos, "L"))
            if c < 4:
                moves.append(Move(pos, "R"))
            if r > 0:
                moves.append(Move(pos, "U"))
            if r < 4:
                moves.append(Move(pos, "D"))
    return tuple(moves)


def apply(s: State, move: Move) -> State:
    # Validate geometry and cube ownership independently in O(1) rather
    # than regenerating the whole legal list for each transition. This is
    # semantically equivalent to membership in legal_moves(s).
    if not isinstance(move, Move):
        raise ValueError(f"illegal move: {move!r}")
    r, c = divmod(move.index, 5)
    if (0 < r < 4 and 0 < c < 4) or s.cells[move.index] not in (0, s.turn) or (
        (move.edge == "L" and c == 0) or
        (move.edge == "R" and c == 4) or
        (move.edge == "U" and r == 0) or
        (move.edge == "D" and r == 4)
    ) or winner(s) is not None:
        raise ValueError(f"illegal move: {move!r}")
    coords: list[tuple[int, int]] = [(r, c)]
    if move.edge == "L":
        coords.extend((r, k) for k in range(c-1, -1, -1))
    elif move.edge == "R":
        coords.extend((r, k) for k in range(c+1, 5))
    elif move.edge == "U":
        coords.extend((k, c) for k in range(r-1, -1, -1))
    else:
        coords.extend((k, c) for k in range(r+1, 5))
    board = list(s.cells)
    for a, b in zip(coords, coords[1:]):
        board[a[0]*5+a[1]] = board[b[0]*5+b[1]]
    end_r, end_c = coords[-1]
    board[5*end_r+end_c] = s.turn
    return State(tuple(board), -s.turn)
