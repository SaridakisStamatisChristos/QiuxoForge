"""Exact low-occupancy exhaustiveness and independent forward-check tests."""
import itertools
import pytest
from quixoforge.model import State, initial, replay
from quixoforge.reference import apply, legal_moves
from quixoforge.bitboard import Bits, apply as bapply, legal_moves as bmoves
from quixoforge.reachability import ReachabilityIndex, occupancy


def test_finite_reachability_zero_and_one_marks_both_starters():
    for start in (-1, 1):
        empty = ReachabilityIndex.build(0, start=start)
        assert empty.state_count == 1
        assert empty.witness(initial(start)) == ()
        one = ReachabilityIndex.build(1, start=start)
        assert one.state_count == 17  # empty plus 16 uniquely marked perimeter squares
        assert one.is_reachable(initial(start))
        assert one.witness(initial(-start)) is None
        for i in range(25):
            cells = [0] * 25
            cells[i] = start
            target = State(tuple(cells), -start)
            assert one.is_reachable(target) == (i // 5 in (0, 4) or i % 5 in (0, 4))
            history = one.witness(target)
            if history is not None:
                assert len(history) == 1
                assert replay(history, start) == target


def test_two_stone_scope_exhaustive_membership_witness_and_optimised_oracle():
    index = ReachabilityIndex.build(2)
    assert index.state_count > 17
    # All structurally valid 0-, 1-, and 2-stone positions: precise membership
    # for each board and both turns, including geometrically unreachable boards.
    for n in range(3):
        for positions in itertools.combinations(range(25), n):
            for marks in itertools.product((-1, 1), repeat=n):
                cells = [0] * 25
                for i, value in zip(positions, marks):
                    cells[i] = value
                for turn in (-1, 1):
                    target = State(tuple(cells), turn)
                    witness = index.witness(target)
                    assert (witness is not None) == index.is_reachable(target)
                    if witness is not None:
                        assert replay(witness) == target
                        # Independent bitboard transition validation of every
                        # step in its shortest constructive certificate.
                        board = Bits.from_state(initial())
                        for step in witness:
                            assert step in bmoves(board)
                            board = bapply(board, step)
                        assert board.state() == target


def test_occupancy_monotonicity_for_every_reachable_small_state():
    index = ReachabilityIndex.build(2)
    assert index.examined_edges >= index.state_count - 1
    for target in index._parents:
        for move in legal_moves(target):
            child = apply(target, move)
            assert occupancy(child) - occupancy(target) in (0, 1)
            if occupancy(child) <= 2:
                assert index.is_reachable(child)


def test_out_of_scope_and_invalid_parameters_are_never_false_negative():
    index = ReachabilityIndex.build(1)
    occupied = [0]*25
    occupied[0] = 1
    occupied[24] = -1
    outside = State(tuple(occupied), 1)
    with pytest.raises(ValueError, match="outside"):
        index.is_reachable(outside)
    with pytest.raises(ValueError, match="outside"):
        index.witness(outside)
    for invalid in (-1, 4, True, 1.5):
        with pytest.raises(ValueError):
            ReachabilityIndex.build(invalid)
    with pytest.raises(ValueError):
        ReachabilityIndex.build(1, start=0)
    with pytest.raises(TypeError):
        index.is_reachable("bad")


def test_three_stone_complete_index_matches_independent_bitboard_graph():
    """Exhaustively compare *sets* of legal reachable states, not just playouts."""
    from collections import deque
    from quixoforge.symmetry import transform

    reference_index = ReachabilityIndex.build(3)
    root = Bits.from_state(initial())
    fast_seen = {root}
    fast_distance = {root: 0}
    frontier = deque([root])
    transitions = 0
    while frontier:
        position = frontier.popleft()
        for action in bmoves(position):
            child = bapply(position, action)
            transitions += 1
            if (child.x | child.o).bit_count() <= 3 and child not in fast_seen:
                fast_seen.add(child)
                fast_distance[child] = fast_distance[position] + 1
                frontier.append(child)

    assert reference_index.state_count == len(fast_seen) == 12_297
    assert reference_index.examined_edges == transitions == 498_328
    assert max(fast_distance.values()) == 18
    # D4 compression agrees on all reachable positions independently.
    from quixoforge.symmetry import canonical as reference_canonical
    from quixoforge.bitboard import canonical as optimized_canonical
    assert len({reference_canonical(pos.state()) for pos in fast_seen}) == 1_576
    assert len({optimized_canonical(pos) for pos in fast_seen}) == 1_576
    # Same cardinality + every optimized state in oracle -> exact set equality.
    for state in fast_seen:
        target = state.state()
        assert reference_index.is_reachable(target)
        assert len(reference_index.witness(target)) == fast_distance[state]
        # All D4 images of *every* reachable low-occupancy state remain reachable.
        for symmetry in range(8):
            assert reference_index.is_reachable(transform(target, symmetry))

    # Legal but geometrically impossible-looking synthetic boards must not be
    # relabeled reachable simply because they pass `State` shape validation.
    three_x_no_o = State((1, 1, 1) + (0,) * 22, -1)
    assert not reference_index.is_reachable(three_x_no_o)
    assert reference_index.witness(three_x_no_o) is None


def test_witness_shortest_path_matches_bitboard_bfs_distance():
    """Independent optimality witness, not merely a replay-valid trace."""
    from collections import deque
    index = ReachabilityIndex.build(2)
    root = Bits.from_state(initial())
    distances = {root: 0}
    queue = deque([root])
    while queue:
        position = queue.popleft()
        for move in bmoves(position):
            child = bapply(position, move)
            if (child.x | child.o).bit_count() <= 2 and child not in distances:
                distances[child] = distances[position] + 1
                queue.append(child)
    assert len(distances) == index.state_count == 485
    for position, minimum in distances.items():
        witness = index.witness(position.state())
        assert witness is not None
        assert len(witness) == minimum


def test_reachability_cli_explicit_three_way_verdict(capsys):
    import json
    from quixoforge.cli import main
    blank = "." * 25
    main(["reach", "--board", blank, "--max-stones", "0"])
    assert json.loads(capsys.readouterr().out)["status"] == "REACHABLE"
    impossible = "X" + "." * 11 + "X" + "." * 12
    main(["reach", "--board", impossible, "--max-stones", "1"])
    assert json.loads(capsys.readouterr().out)["status"] == "OUT_OF_SCOPE"
    center = "." * 12 + "X" + "." * 12
    main(["reach", "--board", center, "--turn", "O", "--max-stones", "1"])
    assert json.loads(capsys.readouterr().out)["status"] == "UNREACHABLE"
    perimeter = "X" + "." * 24
    main(["reach", "--board", perimeter, "--turn", "O", "--max-stones", "1"])
    record = json.loads(capsys.readouterr().out)
    assert record["status"] == "REACHABLE" and len(record["witness"]) == 1
    with pytest.raises(SystemExit):
        main(["reach", "--board", "junk"])
