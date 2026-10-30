import json
from pathlib import Path
import pytest
from quixoforge.generator import certify, generate
from quixoforge.model import Move
from quixoforge.verify_examples import check
from quixoforge.cli import main


def test_certify_existing_replay_and_existing_json_schema(tmp_path):
    base=Path(__file__).resolve().parent.parent/"examples"
    doc=json.loads((base/"unique_immediate_win.json").read_text())
    fresh=certify(tuple(map(Move.parse,doc["history"])),1,unique=True)
    out=tmp_path/"puzzle.json"
    out.write_text(json.dumps(fresh))
    assert check(out)["result"] == "VERIFIED"
    tampered = dict(fresh)
    tampered["minimal_bound"] = 2
    out.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="minimal horizon"):
        check(out)
    tampered = dict(fresh)
    tampered["difficulty"] = "deep-forcing"
    out.write_text(json.dumps(tampered))
    with pytest.raises(ValueError, match="difficulty metadata"):
        check(out)


def test_generator_raises_if_attempts_exhausted():
    with pytest.raises(LookupError):
        generate(seed=1,bound=1,attempts=1,min_plies=0,max_plies=0)
    with pytest.raises(ValueError):
        generate(seed=1,bound=0)
    with pytest.raises(ValueError):
        generate(seed=1,attempts=0)


def test_cli_commands(capsys):
    main(["opponent", "--depth", "1", "--max-nodes", "1000"])
    ai=json.loads(capsys.readouterr().out)
    assert ai["completed_depth"] == 1 and ai["move"] is not None
    main(["team", "--depth", "1", "0:R:2"])
    team=json.loads(capsys.readouterr().out)
    assert team["seat"] == 1 and team["cells"][4] == 2
    doc=json.loads((Path(__file__).resolve().parent.parent/"examples/unique_immediate_win.json").read_text())
    main(["certify", "--depth", "1", "--unique", *doc["history"]])
    assert json.loads(capsys.readouterr().out)["solutions"] == doc["solutions"]
    with pytest.raises(SystemExit):
        main(["team", "foo"])
