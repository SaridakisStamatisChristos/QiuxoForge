import random
import pytest
from quixoforge.model import State, Move, initial, replay, validate_history
from quixoforge import reference, bitboard


def test_opening_has_exactly_44_legal_moves():
    s = initial()
    assert len(reference.legal_moves(s)) == 44
    assert len(bitboard.legal_moves(bitboard.Bits.from_state(s))) == 44
    assert len(set(reference.legal_moves(s))) == 44
    for m in reference.legal_moves(s):
        assert reference.apply(s, m).cells.count(1) == 1


def test_explicit_shift_at_corner_and_middle():
    a = State(tuple([0]*25), 1)
    a = reference.apply(a, Move(0, "R"))
    assert a.cells[4] == 1 and a.cells[0] == 0
    b = reference.apply(a, Move(5, "D"))
    assert b.cells[20] == -1 and b.cells[5] == 0
    assert b.cells[4] == 1


def test_illegal_rules_and_terminal_stop():
    s = initial()
    for m in (Move(12, "R"), Move(0, "L"), Move(0, "U")):
        with pytest.raises(ValueError): reference.apply(s, m)
    s = reference.apply(s, Move(0, "R"))
    # Opponent cannot pick player's cube.
    with pytest.raises(ValueError): reference.apply(s, Move(4, "L"))
    terminal = State((1,)*5+(0,)*20, -1)
    assert reference.winner(terminal) == 1
    assert not reference.legal_moves(terminal)
    with pytest.raises(ValueError): reference.apply(terminal, Move(5, "R"))


def test_opponent_line_precedes_movers_line_on_simultaneous_wins():
    # X just moved; next player O. If both rows win, X loses, O wins.
    s = State((1,)*5+(-1,)*5+(0,)*15, -1)
    assert reference.winner(s) == -1
    assert bitboard.winner(bitboard.Bits.from_state(s)) == -1
    assert reference.winner(State(s.cells, 1)) == 1  # O just moved instead


def test_state_validation_vs_certified_reachability():
    for values, turn in [((0,)*24, 1), ((0,)*25, 0), ((0,)*24+(2,), 1), ([0]*25,1)]:
        with pytest.raises(ValueError): State(values, turn)
    for invalid in (True, 1.0, "X"):
        with pytest.raises(ValueError): initial(invalid)
    hist = (Move(0, "R"), Move(5, "D"))
    s = replay(hist)
    assert validate_history(s, hist)
    assert not validate_history(initial(), hist)
    with pytest.raises(ValueError): replay((Move(0, "U"),))
    with pytest.raises(ValueError): Move.parse("bad")


def test_bitboard_invalid_masks_and_wrong_player():
    for x, o in ((1,1), (-1,0), (1<<25,0)):
        with pytest.raises(ValueError): bitboard.Bits(x,o,1)
    s = reference.apply(initial(), Move(0,"R"))
    with pytest.raises(ValueError): bitboard.apply(bitboard.Bits.from_state(s), Move(4,"L"))


def test_independent_differential_all_two_ply_branches():
    root = initial()
    count = 0
    for m in reference.legal_moves(root):
        a = reference.apply(root, m)
        assert a == bitboard.apply(bitboard.Bits.from_state(root), m).state()
        ba = bitboard.Bits.from_state(a)
        assert set(reference.legal_moves(a)) == set(bitboard.legal_moves(ba))
        for n in reference.legal_moves(a):
            b = reference.apply(a, n)
            assert b == bitboard.apply(ba,n).state()
            assert reference.winner(b) == bitboard.winner(bitboard.Bits.from_state(b))
            count += 1
    assert count > 1300


def test_random_replayed_states_parity():
    rng = random.Random(20261030)
    for _ in range(65):
        state = initial()
        for ply in range(32):
            bs = bitboard.Bits.from_state(state)
            assert bs.state() == state
            assert reference.winner(state) == bitboard.winner(bs)
            assert set(reference.legal_moves(state)) == set(bitboard.legal_moves(bs))
            moves = reference.legal_moves(state)
            if not moves: break
            m = rng.choice(moves)
            assert reference.apply(state, m) == bitboard.apply(bs,m).state()
            state = reference.apply(state, m)
