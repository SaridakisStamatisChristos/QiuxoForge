from copy import deepcopy
import pytest
from quixoforge.model import State, Move, initial, replay
from quixoforge.reference import legal_moves, apply
from quixoforge.solver import ReferenceSolver, BitboardSolver, Result, winning_moves
from quixoforge.proof import produce, verify
from quixoforge.puzzles import Puzzle, audit

# A concrete, legal sequence discovered with random.Random(7197), then pinned.
FORCED_ONE = (
    "2:D", "3:D", "0:R", "3:D", "22:U", "19:D", "2:R", "9:U", "3:L", "15:U", "3:L", "2:D",
    "21:R", "4:D", "20:R", "20:R", "10:R", "3:R", "3:D", "20:R", "9:U", "10:R", "19:L",
)


def example():
    return replay(tuple(Move.parse(x) for x in FORCED_ONE))


def test_initial_depths_are_not_false_draws():
    for depth in range(3):
        assert ReferenceSolver().solve(initial(),depth) == Result.UNKNOWN
        assert BitboardSolver().solve(initial(),depth) == Result.UNKNOWN


def test_terminals_and_validation():
    xwin = State((1,)*5+(0,)*20,-1)
    assert ReferenceSolver().solve(xwin,0) == Result.LOSS
    assert BitboardSolver().solve(xwin,0) == Result.LOSS
    assert ReferenceSolver().solve(State(xwin.cells,1),0) == Result.WIN
    for solver in (ReferenceSolver(), BitboardSolver()):
        with pytest.raises(ValueError): solver.solve(initial(),-1)
        with pytest.raises(ValueError): solver.solve(initial(),1.5)


def test_replayed_unique_immediate_win_and_independent_certificate():
    s=example()
    a=ReferenceSolver(); b=BitboardSolver()
    assert a.solve(s,1) == b.solve(s,1) == Result.WIN
    assert winning_moves(s,1,a) == winning_moves(s,1,b) == (Move(2,"D"),)
    cert=produce(s,1,a)
    assert verify(s,1,cert) == Result.WIN
    assert audit(Puzzle(tuple(Move.parse(m) for m in FORCED_ONE),1),require_unique=True).difficulty == "immediate"


def test_untrusted_certificate_falsification():
    s=example()
    cert=produce(s,1)
    corrupt=deepcopy(cert)
    corrupt["move"]="0:R"
    with pytest.raises(ValueError):verify(s,1,corrupt)
    with pytest.raises(ValueError):verify(initial(),0,cert)
    with pytest.raises(ValueError):produce(initial(),1)
    with pytest.raises(ValueError):audit(Puzzle((),1))
    with pytest.raises(ValueError): audit(Puzzle(tuple(Move.parse(m) for m in FORCED_ONE),0))


def test_loss_requires_every_opponent_reply_in_certificate():
    # After the unique winning X action, terminal O-to-move LOSS leaf.
    child=apply(example(),Move(2,"D"))
    assert verify(child,0,produce(child,0)) == Result.LOSS
    with pytest.raises(ValueError):verify(child,0,{"outcome":"WIN","terminal":True})


def test_generic_game_interface_replaces_rules():
    class Toy:
        def legal_moves(self,s):return ("a",) if s < 2 else ()
        def apply(self,s,m):return s+1
        def winner(self,s):return 1 if s==2 else None
        def turn(self,s):return 1 if s%2==0 else -1
        def cache_key(self,s):return s
    assert ReferenceSolver(Toy()).solve(0,2)==Result.WIN


def test_certified_depth_three_forcing_puzzle_and_mutation():
    import json
    from pathlib import Path
    from quixoforge.verify_examples import check
    base=Path(__file__).resolve().parent.parent / "examples"
    f=base/"unique_forcing_win_3.json"
    doc=json.loads(f.read_text())
    outcome=check(f)
    assert outcome["minimal_bound"]==3
    assert doc["solutions"]==["10:R"]
    s=replay([Move.parse(m) for m in doc["history"]])
    broken=deepcopy(doc["proof"])
    # A LOSS node must enumerate every response. Remove one and reject it.
    loss_node=broken["child"]
    assert loss_node["outcome"]=="LOSS" and len(loss_node["replies"])>1
    loss_node["replies"].pop(next(iter(loss_node["replies"])))
    with pytest.raises(ValueError,match="missing or unexpected"):
        verify(s,3,broken)


def test_fixture_verifier_checks_both_replay_proofs():
    from pathlib import Path
    from quixoforge.verify_examples import check
    base=Path(__file__).resolve().parent.parent / "examples"
    assert check(base/"unique_immediate_win.json")["result"]=="VERIFIED"
