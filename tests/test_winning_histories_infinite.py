"""Constructive 5x5 theorem: countably infinitely many first-win histories."""
from quixoforge.model import Move, initial
from quixoforge import reference


def test_winning_game_histories_have_exactly_countable_infinite_cardinality():
    prefix = ("24:U", "3:R")
    cycle = ("3:R", "3:R")
    suffix = ("2:R", "3:R", "1:R", "3:D", "5:U", "23:U", "23:U")

    def checked_replay(seq):
        state = initial()
        for notation in seq:
            assert reference.winner(state) is None, "history played past terminal"
            move = Move.parse(notation)
            assert move in reference.legal_moves(state), (notation, state)
            state = reference.apply(state, move)
        return state

    parent = checked_replay(prefix)
    assert reference.winner(parent) is None
    assert checked_replay(prefix + cycle) == parent
    winning_board = checked_replay(prefix + suffix)
    assert reference.winner(winning_board) == 1
    assert "".join("." if x == 0 else "X" if x == 1 else "O"
                   for x in winning_board.cells) == "XXXXX...O................"
    for n in (0, 1, 2, 10, 100):
        path = prefix + cycle * n + suffix
        assert len(path) == 9 + 2*n
        assert checked_replay(path) == winning_board
    # The induction over n >= 0 is mathematical: the cycle is an exact
    # state identity with no terminal intermediate. Tests check examples.
    # The set of all finite words over the 44-move alphabet is countable;
    # we exhibit an injection from natural n to distinct winning words.
