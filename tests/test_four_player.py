"""Independent transition oracle and adversarial four-player rule tests."""
import random
import pytest

from quixoforge.model import Move, X, O
from quixoforge.teams import (TeamState, TeamMove, PASS, FourPlayerGame,
                              initial, legal_moves, apply, winner, replay)
from quixoforge.solver import ReferenceSolver, Result


def independent(s, action):
    """Row/column list delete+insert oracle independent from in-place shifts."""
    if action == PASS:
        assert legal_moves(s) == (PASS,)
        return TeamState(s.cells, (s.seat + 1) % 4, s.ply + 1)
    i = action.move.index
    r, c = divmod(i, 5)
    board = list(s.cells)
    if action.move.edge in ("L", "R"):
        row = board[5*r:5*r+5]
        row.pop(c)
        if action.move.edge == "L":
            row.insert(0, action.point)
        else:
            row.append(action.point)
        board[5*r:5*r+5] = row
    else:
        col = [board[5*k+c] for k in range(5)]
        col.pop(r)
        if action.move.edge == "U":
            col.insert(0, action.point)
        else:
            col.append(action.point)
        for k, v in enumerate(col):
            board[5*k+c] = v
    return TeamState(tuple(board), (s.seat + 1) % 4, s.ply + 1)


def test_first_round_and_partner_orientation():
    s = initial()
    assert len(legal_moves(s)) == 88
    first = TeamMove(Move(0, "R"), 2)
    assert first in legal_moves(s)
    s = apply(s, first)
    assert s.cells[4] == 2
    assert s.seat == 1
    # Teammate may not reclaim marked cube within the first round.
    for _ in range(3):
        m = legal_moves(s)[0]
        assert s.cells[m.move.index] == -1
        s = apply(s, m)
    assert s.seat == 0 and s.ply == 4
    assert all(m.move.index != 4 for m in legal_moves(s) if m != PASS)
    s = apply(s, legal_moves(s)[0])
    s = apply(s, legal_moves(s)[0])
    assert s.seat == 2
    if s.cells[4] == 2:
        assert any(m.move.index == 4 for m in legal_moves(s) if m != PASS)


def test_full_differential_random_legal_games():
    for seed in range(64):
        rng = random.Random(seed)
        s = initial()
        history = []
        for _ in range(95):
            if winner(s) is not None:
                break
            legal = legal_moves(s)
            assert legal
            choice = rng.choice(legal)
            outcome = apply(s, choice)
            assert outcome == independent(s, choice)
            assert all(v == -1 or v % 2 in (0, 1) for v in outcome.cells)
            history.append(choice)
            s = outcome
        assert replay(history) == s


def test_pass_is_forced_and_terminal_forbids_moves():
    # After phase 4, every outer cube is oriented toward another seat.
    cells = [1] * 25  # O-owned, all points to seat 1 (not current seat 0)
    # Introduce just one X-owned cube pointing away from seat 0.
    cells[0] = 2
    s = TeamState(tuple(cells), 0, 4)
    # No X line exists, O has multiple lines => winning O; passes forbidden.
    assert winner(s) == O and legal_moves(s) == ()
    with pytest.raises(ValueError):
        apply(s, PASS)
    # Fill a board without lines and with zero blank/seat-0 pointers.
    # Team X owns cubes pointing to seat 2; seat 0 cannot select any.
    b = [2 if (r+c) % 2 == 0 else 1 for r in range(5) for c in range(5)]
    # Checkerboard with odd length has a diagonal X line, so break center.
    b[12] = 1
    b[0] = 1
    b[24] = 1
    # Never assume arbitrary constructed board is nonterminal; use an
    # explicit search for an admissible nonwinning full board.
    rng = random.Random(671)
    for _ in range(1000):
        b = [rng.choice((1, 2)) for _ in range(25)]
        t = TeamState(tuple(b), 0, 4)
        if winner(t) is None:
            assert legal_moves(t) == (PASS,)
            assert apply(t, PASS).cells == t.cells
            assert apply(t, PASS).seat == 1
            with pytest.raises(ValueError):
                apply(t, TeamMove(Move(0, "R"), 0))
            break
    else:
        raise AssertionError("could not construct legal structural pass state")


def test_team_validation_and_solver_adapter():
    with pytest.raises(ValueError): TeamState((0,) * 25, 3, 0)
    with pytest.raises(ValueError): TeamState((-1,) * 25, 0, -1)
    with pytest.raises(ValueError): TeamMove(Move(0, "R"), 4)
    s = initial()
    for d in (0, 1):
        assert ReferenceSolver(FourPlayerGame()).solve(s, d) == Result.UNKNOWN
    assert FourPlayerGame().cache_key(TeamState((-1,) * 25, 0, 4)) == FourPlayerGame().cache_key(TeamState((-1,) * 25, 0, 8))
