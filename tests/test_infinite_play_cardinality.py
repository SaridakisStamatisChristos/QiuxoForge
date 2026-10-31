"""Independent executable witness for continuum-many infinite Quixo games.

We demonstrate two *different* legal nonterminal two-ply cycles through
the same X-to-move state. Each binary choice yields another entire
distinct infinite sequence with no completed winning line; all binary
infinite sequences thus inject into legal infinite nonterminating plays.
A finite action alphabet bounds cardinality above by the continuum.
No repetition-draw rule is assumed.
"""
from itertools import product

from quixoforge.model import Move, initial
from quixoforge.reference import apply, legal_moves, winner

PREFIX = ("24:U", "3:R", "20:R", "20:R")
TOP_CYCLE = ("3:R", "3:R")
BOTTOM_CYCLE = ("23:R", "23:R")


def replay_nonterminal(initial_state, moves):
    state = initial_state
    for action in moves:
        assert winner(state) is None
        move = Move.parse(action)
        assert move in legal_moves(state), f"illegal: {move}"
        state = apply(state, move)
        assert winner(state) is None, f"early win from {move}"
    return state


def test_two_distinct_reversible_cycles_at_one_nonterminal_5x5_root():
    root = replay_nonterminal(initial(), PREFIX)
    assert root.turn == 1
    assert str(root) == "...XO\n.....\n.....\n.....\n...XO"
    assert TOP_CYCLE != BOTTOM_CYCLE
    assert replay_nonterminal(root, TOP_CYCLE) == root
    assert replay_nonterminal(root, BOTTOM_CYCLE) == root


def test_binary_words_are_distinct_legal_nonterminating_history_prefixes():
    root = replay_nonterminal(initial(), PREFIX)
    for length in range(7):
        seen = set()
        for bits in product((0, 1), repeat=length):
            actions = tuple(
                step
                for bit in bits
                for step in (TOP_CYCLE if bit == 0 else BOTTOM_CYCLE)
            )
            assert replay_nonterminal(root, actions) == root
            assert actions not in seen
            seen.add(actions)
        assert len(seen) == 2**length

    # The infinite result is a rigorous induction, not an unbounded test:
    # at each 2-ply block the complete board/turn returns to 'root'
    # without a terminal win. The action word differs at its first
    # unequal binary symbol. Thus {0,1}^N embeds in infinite plays.
    # All infinite legal Quixo action words belong to A^N for finite A
    # (44 candidate perimeter selection/insertion actions), so the
    # exact cardinality is 2^(aleph_0).
