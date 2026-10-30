"""Independent adversarial oracles for the exact 3x3 strong solution."""
from collections import Counter
from dataclasses import replace
from hashlib import sha256
from importlib.resources import files
import json
import random
import pytest

from quixoforge.model import Move
from quixoforge import reference, bitboard
from quixoforge.bitboard import Bits
from quixoforge.retrograde import Outcome, solve, verify
from quixoforge.tablebase import Tablebase, TABLEBASE_SHA256
from quixoforge.variants import VariantState, VariantBits, VariantReference, VariantBitboard, initial


def test_exact_packaged_full_solution_and_opening_policy():
    tb = Tablebase.load()
    assert tb.states == 32027
    start = initial(3)
    assert tb.lookup(start).outcome == Outcome.WIN
    assert tb.lookup(start).remoteness == 7
    assert len(tb.moves(start)) == 20  # 20 optimal first moves, not 44 for 5x5
    sample = VariantReference(3).apply(start, tb.moves(start)[0])
    assert tb.lookup(sample).outcome == Outcome.LOSS
    assert tb.lookup(sample).remoteness == 6
    assert sha256(files('quixoforge').joinpath('data/quixo3.tbl.gz').read_bytes()).hexdigest() == TABLEBASE_SHA256


def test_every_packed_value_and_remoteness_is_locally_consistent():
    tb = Tablebase.load()
    game = VariantBitboard(3)
    counts = Counter()
    # Check all tablebase entries with a separate bitmask move oracle; this
    # never calls the reference implementation or retrograde solver.
    for (x, o, turn), value in tb._entries.items():
        state = VariantBits(x, o, turn, 3)
        terminal = game.winner(state)
        counts[value.outcome] += 1
        if terminal is not None:
            assert value.remoteness == 0
            assert value.outcome == (Outcome.WIN if terminal == turn else Outcome.LOSS)
        else:
            children = [tb.lookup(game.apply(state, m)) for m in game.legal_moves(state)]
            if value.outcome == Outcome.WIN:
                assert value.remoteness == 1 + min(v.remoteness for v in children if v.outcome == Outcome.LOSS)
            elif value.outcome == Outcome.LOSS:
                assert all(v.outcome == Outcome.WIN for v in children)
                assert value.remoteness == 1 + max(v.remoteness for v in children)
            else:
                assert value.remoteness is None
                assert not any(v.outcome == Outcome.LOSS for v in children)
                assert any(v.outcome == Outcome.NONFORCED for v in children)
    assert counts == {Outcome.WIN: 20247, Outcome.LOSS: 11780}


def test_tablebase_data_rejects_corruption_and_invalid_queries():
    data = files('quixoforge').joinpath('data/quixo3.tbl.gz').read_bytes()
    tampered = bytearray(data)
    tampered[-4] ^= 0x01
    with pytest.raises(ValueError, match='checksum'):
        Tablebase(bytes(tampered))
    tb = Tablebase.load()
    with pytest.raises(ValueError, match='3x3'):
        tb.lookup(initial(5))
    with pytest.raises(ValueError, match='reachable'):
        tb.lookup(VariantState((1,)+(0,)*8, 1, 3))  # X mark but still X turn
    with pytest.raises(ValueError, match='different'):
        VariantBitboard(4).winner(VariantBits.from_state(initial(3)))


def test_rule_oracles_independent_at_all_sizes():
    rng = random.Random(27330)
    for n in (2,3,4,5):
        a,b = VariantReference(n),VariantBitboard(n)
        for i in range(32):
            state = initial(n)
            for step in range(15):
                bits = VariantBits.from_state(state)
                assert a.winner(state) == b.winner(bits)
                assert set(a.legal_moves(state)) == set(b.legal_moves(bits))
                for m in a.legal_moves(state):
                    assert a.apply(state,m) == b.apply(bits,m).state()
                if n == 5:
                    base = bitboard.Bits.from_state(__import__('quixoforge').State(state.cells,state.turn))
                    assert a.winner(state) == reference.winner(base.state()) == bitboard.winner(base)
                    assert set(a.legal_moves(state)) == set(reference.legal_moves(base.state()))
                moves = a.legal_moves(state)
                if not moves: break
                state = a.apply(state,rng.choice(moves))


def test_generic_nonforced_cycle_is_not_a_fabricated_win_or_loss():
    class Cycle:
        def legal_moves(self,s): return ('again',)
        def apply(self,s,m): return s
        def winner(self,s): return None
        def turn(self,s): return 1
        def cache_key(self,s): return s
    game=Cycle()
    result=solve(game, 0)
    assert result.outcome(0) == Outcome.NONFORCED
    assert 0 not in result.remoteness
    assert result.best_successor(0) == 0
    verify(game,result)


def test_generic_win_escapes_cycle_and_budget_never_fabricates_nonforced():
    class WinCycle:
        def legal_moves(self,s): return ('self','win') if s == 0 else ()
        def apply(self,s,m): return 0 if m=='self' else 1
        def winner(self,s): return 1 if s==1 else None
        def turn(self,s): return 1 if s==0 else -1
        def cache_key(self,s): return s
    game=WinCycle()
    with pytest.raises(ValueError, match='max_states'):
        solve(game,0,max_states=1)
    result=solve(game,0,max_states=2)
    assert result.outcome(0) == Outcome.WIN
    assert result.remoteness[0] == 1
    assert result.best_successor(0) == 1
    verify(game,result)


def test_tablebase_symmetry_covariance_full_3x3():
    tb = Tablebase.load()
    def transform(x,o,k):
        a=b=0
        for i in range(9):
            r,c=divmod(i,3)
            for _ in range(k % 4): r,c = c,2-r
            if k>=4: c=2-c
            j=3*r+c
            if x&(1<<i): a|=1<<j
            if o&(1<<i): b|=1<<j
        return a,b
    for (x,o,t),value in tb._entries.items():
        for k in range(8):
            nx,no=transform(x,o,k)
            assert tb.lookup(VariantBits(nx,no,t,3)) == value
