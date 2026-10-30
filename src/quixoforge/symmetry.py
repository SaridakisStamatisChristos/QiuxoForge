"""D4 rotations/reflections of the 5x5 square, preserving player colors."""
from __future__ import annotations
from .model import State, Move


def _transforms() -> tuple[tuple[int, ...], ...]:
    maps = []
    for reflected in (False, True):
        for turns in range(4):
            m = []
            for i in range(25):
                r, c = divmod(i, 5)
                if reflected:
                    c = 4-c
                for _ in range(turns):
                    r, c = c, 4-r
                m.append(5*r+c)
            maps.append(tuple(m))
    assert len(set(maps)) == 8
    return tuple(maps)

D4 = _transforms()  # each permutation maps old index to new index


def transform(s: State, k: int) -> State:
    mapping = D4[k]
    out = [0]*25
    for old, new in enumerate(mapping):
        out[new] = s.cells[old]
    return State(tuple(out), s.turn)


def transform_move(move: Move, k: int) -> Move:
    m = D4[k]
    r, c = divmod(move.index, 5)
    end = {"L": 5*r, "R": 5*r+4, "U": c, "D": 20+c}[move.edge]
    new_src, new_end = m[move.index], m[end]
    sr, sc = divmod(new_src, 5)
    er, ec = divmod(new_end, 5)
    if sr == er and ec == 0:
        side = "L"
    elif sr == er and ec == 4:
        side = "R"
    elif sc == ec and er == 0:
        side = "U"
    elif sc == ec and er == 4:
        side = "D"
    else:
        raise AssertionError("D4 transformation did not preserve board extremity")
    return Move(new_src, side)


def canonical(s: State) -> tuple[int, bytes]:
    """Unique transposition key for the D4 orbit; no unsupported color swap."""
    # bytes 0=O, 1=empty, 2=X, so no negative bytes.
    candidates = []
    for m in D4:
        out = bytearray(25)
        for old, new in enumerate(m):
            out[new] = s.cells[old] + 1
        candidates.append(bytes(out))
    return (s.turn, min(candidates))
