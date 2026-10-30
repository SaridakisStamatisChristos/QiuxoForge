import random
import pytest
from quixoforge import teams, team_bitboard
from quixoforge.solver import ReferenceSolver


def test_exhaustive_first_round_actions():
    s=teams.initial()
    b=team_bitboard.TeamBits.from_state(s)
    assert len(teams.legal_moves(s)) == 88
    assert teams.legal_moves(s) == team_bitboard.legal_moves(b)
    for action in teams.legal_moves(s):
        assert team_bitboard.apply(b, action).state() == teams.apply(s, action)


def test_random_independent_four_player_paths_and_legality():
    for seed in range(60):
        rng=random.Random(seed+305)
        s=teams.initial()
        b=team_bitboard.TeamBits.from_state(s)
        for t in range(80):
            assert s == b.state()
            assert teams.winner(s) == team_bitboard.winner(b)
            assert set(teams.legal_moves(s)) == set(team_bitboard.legal_moves(b))
            if teams.winner(s) is not None:
                break
            a=rng.choice(teams.legal_moves(s))
            s=teams.apply(s,a)
            b=team_bitboard.apply(b,a)
        assert s == b.state()


def test_exact_bounded_solvers_agree_on_team_games():
    for seed in range(8):
        r=random.Random(seed*101)
        s=teams.initial()
        for _ in range(12):
            if teams.winner(s) is not None:
                break
            s=teams.apply(s, r.choice(teams.legal_moves(s)))
        b=team_bitboard.TeamBits.from_state(s)
        for d in range(3):
            assert ReferenceSolver(teams.FourPlayerGame()).solve(s,d) == ReferenceSolver(team_bitboard.BitboardFourPlayerGame()).solve(b,d)


def test_overlap_and_invalid_pass_rejected():
    with pytest.raises(ValueError): team_bitboard.TeamBits((1,1,0,0),0,0)
    with pytest.raises(ValueError): team_bitboard.TeamBits((1<<25,0,0,0),0,0)
    with pytest.raises(ValueError): team_bitboard.TeamBits((0,0,0,0),1,0)
    with pytest.raises(ValueError): team_bitboard.apply(team_bitboard.TeamBits.from_state(teams.initial()),teams.PASS)
