import random
from quixoforge.model import initial
from quixoforge.reference import legal_moves,apply,winner
from quixoforge.bitboard import Bits, canonical as bit_canonical
from quixoforge.symmetry import D4, canonical,transform,transform_move


def test_dihedral_permutations_are_eight_distinct_bijections():
    assert len(D4) == len(set(D4)) == 8
    for mapping in D4:
        assert set(mapping) == set(range(25))


def test_symmetry_commutes_with_every_initial_move():
    s = initial()
    for m in legal_moves(s):
        for k in range(8):
            tm = transform_move(m,k)
            assert tm in legal_moves(transform(s,k))
            assert transform(apply(s,m),k) == apply(transform(s,k),tm)


def test_symmetry_equivariance_midgame_and_canonical_stability():
    rng = random.Random(941)
    for _ in range(20):
        s = initial()
        for i in range(rng.randrange(5,22)):
            lm = legal_moves(s)
            if not lm:break
            s = apply(s,rng.choice(lm))
        for k in range(8):
            t = transform(s,k)
            assert canonical(t) == canonical(s)
            assert bit_canonical(Bits.from_state(t)) == bit_canonical(Bits.from_state(s))
            assert winner(t) == winner(s)
            assert {transform_move(m,k) for m in legal_moves(s)} == set(legal_moves(t))
            for m in legal_moves(s):
                assert transform(apply(s,m),k) == apply(t,transform_move(m,k))
