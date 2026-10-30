"""Independent exhaustive minimax oracle for the alpha-beta heuristic score."""
from random import Random
import pytest
from quixoforge import reference
from quixoforge.bitboard import Bits
from quixoforge.engine import AlphaBetaEngine, MATE
from quixoforge.model import initial
from quixoforge.symmetry import transform


def brute(s, depth):
    w = reference.winner(s)
    if w is not None:
        return (MATE+depth) if w == s.turn else (-MATE-depth)
    moves = reference.legal_moves(s)
    if depth == 0 or not moves:
        return AlphaBetaEngine.evaluate(Bits.from_state(s))
    return max(-brute(reference.apply(s, m), depth-1) for m in moves)


def positions():
    rng = Random(3949)
    for length in (0, 2, 5, 10, 18, 25):
        s = initial()
        for _ in range(length):
            if reference.winner(s) is not None:
                break
            s = reference.apply(s, rng.choice(reference.legal_moves(s)))
        if reference.winner(s) is None:
            yield s


def test_alpha_beta_matches_independent_minimax_for_every_depth():
    for s in positions():
        for depth in (1, 2):
            engine = AlphaBetaEngine()
            result = engine.recommend(s, depth=depth)
            assert not result.aborted and result.completed_depth == depth
            assert result.move in reference.legal_moves(s)
            assert result.score == brute(s, depth)
            assert result.pv[0] == result.move
            current = s
            for m in result.pv:
                assert m in reference.legal_moves(current)
                current = reference.apply(current, m)


def test_d4_invariant_scores():
    s = next(s for s in positions() if sum(c != 0 for c in s.cells) >= 5)
    expected = AlphaBetaEngine().recommend(s, depth=2).score
    assert all(AlphaBetaEngine().recommend(transform(s,k), depth=2).score == expected for k in range(8))


def test_interrupted_iteration_discards_partial():
    s = initial()
    e = AlphaBetaEngine()
    a = e.recommend(s, depth=5, max_nodes=120)
    assert a.aborted and a.completed_depth < 5
    if a.move is not None:
        assert a.score == brute(s, a.completed_depth)
        assert a.move in reference.legal_moves(s)
    b = AlphaBetaEngine().recommend(s, depth=1)
    assert b.completed_depth == 1
    assert b.score == brute(s, 1)
    for kwargs in ({"depth": -1}, {"depth": 0}, {"depth": 2, "max_nodes": 0}, {"depth": 2, "max_nodes": 1.2}):
        with pytest.raises(ValueError):
            AlphaBetaEngine().recommend(s, **kwargs)


def test_terminal_handling_and_bitboards():
    from quixoforge.model import State
    s = State((1,) * 5 + (0,) * 20, -1)
    assert AlphaBetaEngine().recommend(s).move is None
    assert AlphaBetaEngine().recommend(Bits.from_state(initial()), depth=1).move is not None
