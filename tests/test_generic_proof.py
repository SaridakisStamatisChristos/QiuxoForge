import random
from copy import deepcopy
import pytest
from quixoforge import reference, teams, team_bitboard
from quixoforge.bitboard import Bits
from quixoforge.model import Move
from quixoforge.solver import ReferenceSolver, Result, ReferenceGame
from quixoforge import generic_proof


def test_two_player_equivalence_and_corruption():
    from quixoforge.proof import verify as old_verify
    from quixoforge.model import replay
    history = ("2:D", "3:D", "0:R", "3:D", "22:U", "19:D", "2:R", "9:U", "3:L", "15:U", "3:L", "2:D", "21:R", "4:D", "20:R", "20:R", "10:R", "3:R", "3:D", "20:R", "9:U", "10:R", "19:L")
    s=replay(map(Move.parse,history))
    proof=generic_proof.produce(ReferenceGame(),s,1)
    assert generic_proof.verify(ReferenceGame(),s,1,proof) == Result.WIN
    assert old_verify(s,1,proof) == Result.WIN
    bad=deepcopy(proof);bad["move"]="0:L"
    with pytest.raises(ValueError):generic_proof.verify(ReferenceGame(),s,1,bad)


def test_four_player_game_independent_checked_proof_and_corruption():
    rng=random.Random(61091)
    source=teams.FourPlayerGame()
    fast=team_bitboard.BitboardFourPlayerGame()
    found=False
    for _ in range(45):
        s=teams.initial()
        for _ in range(34):
            if teams.winner(s) is not None:break
            candidate=next((m for m in teams.legal_moves(s)
                             if teams.winner(teams.apply(s,m)) == s.turn),None)
            if candidate is not None:
                b=team_bitboard.TeamBits.from_state(s)
                assert ReferenceSolver(source).solve(s,1) == ReferenceSolver(fast).solve(b,1) == Result.WIN
                cert=generic_proof.produce(fast,b,1,ReferenceSolver(fast))
                assert generic_proof.verify(source,s,1,cert) == Result.WIN
                corrupt=deepcopy(cert)
                corrupt["child"]["outcome"]="WIN"
                with pytest.raises(ValueError):generic_proof.verify(source,s,1,corrupt)
                found=True
                break
            s=teams.apply(s,rng.choice(teams.legal_moves(s)))
        if found:break
    assert found, "seeded legal games must contain a 4-player mate-in-one"


def test_replayed_four_player_certificate_and_mutation(tmp_path):
    import json
    from pathlib import Path
    from quixoforge.team_puzzles import check, parse_action, certify
    base=Path(__file__).resolve().parent.parent/"examples/team_forcing_one.json"
    doc=json.loads(base.read_text())
    assert check(base)["result"] == "VERIFIED"
    fresh=certify(tuple(parse_action(m) for m in doc["history"]),1)
    assert set(fresh["solutions"]) == set(doc["solutions"])
    target=tmp_path/"mutated.json"
    tampered=deepcopy(doc)
    tampered["solutions"]=["0:R:0"]
    target.write_text(json.dumps(tampered))
    with pytest.raises(ValueError):check(target)
    tampered=deepcopy(doc)
    tampered["proof"]["child"]["outcome"]="WIN"
    target.write_text(json.dumps(tampered))
    with pytest.raises(ValueError):check(target)
