"""Adversarial finite-horizon checks against independent tuple-array Quixo rules."""
from random import Random
import pytest

from quixoforge.model import State, X, O
from quixoforge import reference
from quixoforge.census5_tactical import _winner
from quixoforge.census5_forced3 import (
    _TEMPLATE, potential_winning_action_indices, immediate_win_indices,
    forcing_first_indices_three,
)


def test_threat_preimages_complete_against_independent_reference_oracle():
    rng = Random(0x51AB)
    for _ in range(2000):
        k = rng.randrange(0, 8)
        spots = rng.sample(range(25), k)
        split = rng.randrange(k + 1)
        cells = [0] * 25
        for i in spots[:split]:
            cells[i] = X
        for i in spots[split:]:
            cells[i] = O
        side = rng.choice((X, O))
        state = State(tuple(cells), side)
        mask_x = sum(1 << i for i, v in enumerate(cells) if v == X)
        mask_o = sum(1 << i for i, v in enumerate(cells) if v == O)
        bits = mask_x, mask_o, side
        if reference.winner(state) is not None:
            assert not immediate_win_indices(bits)
            continue
        oracle = {
            m for m in reference.legal_moves(state)
            if reference.winner(reference.apply(state, m)) == side
        }
        fast = {_TEMPLATE[i][0] for i in immediate_win_indices(bits)}
        assert fast == oracle


def test_threat_rejects_invalid_masks_and_move_set_is_exact():
    assert len(_TEMPLATE) == 44
    for invalid in (-1, 1 << 25, 2.0, True):
        with pytest.raises(ValueError):
            potential_winning_action_indices(invalid)
    blank = (0, 0, X)
    assert immediate_win_indices(blank) == ()
    assert forcing_first_indices_three(blank) == ()


def test_forced_three_is_not_restricted_to_the_five_cube_future_domain():
    # Five-move puzzles must be evaluated with the actual, full board.
    # The forcing check has no 'max_stones' argument and thus never censors
    # a defender move that creates a sixth or seventh mark.
    position = (0, 0, X)
    assert forcing_first_indices_three(position) == ()
    assert _winner(position) is None


def test_forced_three_matches_independent_full_reference_on_reachable_k6_samples():
    """Reference enumerates every attacker/defender/attacker legal action."""
    from quixoforge.model import initial
    from quixoforge.bitboard import Bits
    rng = Random(0x5C0606)
    tested = 0
    for trial in range(18):
        state = initial()
        for ply in range(8 + trial % 7):
            options = reference.legal_moves(state)
            if not options:
                break
            # Try to sample six-cube reachable states, not arbitrary drawings.
            blanks = [m for m in options if state.cells[m.index] == 0]
            choice = rng.choice(blanks if blanks and state.cells.count(0) > 19
                                and rng.random() < .75 else options)
            state = reference.apply(state, choice)
            if state.cells.count(0) < 19:
                break
        if reference.winner(state) is not None:
            continue
        bit = Bits.from_state(state)
        fast = {_TEMPLATE[i][0] for i in forcing_first_indices_three(
            (bit.x, bit.o, bit.turn)
        )}
        owner = state.turn
        expected = set()
        for first in reference.legal_moves(state):
            after = reference.apply(state, first)
            if reference.winner(after) == owner:
                expected.add(first)
                continue
            if reference.winner(after) is not None:
                continue
            forced = True
            for defender in reference.legal_moves(after):
                middle = reference.apply(after, defender)
                result = reference.winner(middle)
                if result == owner:
                    continue
                if result is not None or not any(
                    reference.winner(reference.apply(middle, last)) == owner
                    for last in reference.legal_moves(middle)
                ):
                    forced = False
                    break
            if forced:
                expected.add(first)
        assert fast == expected
        tested += 1
    assert tested >= 12
