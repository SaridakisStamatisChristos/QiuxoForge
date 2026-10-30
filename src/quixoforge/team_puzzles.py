"""Complete, independent certification of four-seat two-team tactical puzzles.

A team puzzle contains a replayable four-seat move list and an AND/OR tree
produced from optimized four-mask transitions, then verified against the
separate reference list-based team transition implementation.
"""
from __future__ import annotations
import json
from pathlib import Path
from . import teams, team_bitboard, generic_proof
from .solver import ReferenceSolver, Result


def parse_action(token: str) -> teams.TeamAction:
    if token == "PASS":
        return teams.PASS
    left, delim, point = token.rpartition(":")
    if not delim or not point.isdecimal():
        raise ValueError(f"invalid team action: {token!r}")
    from .model import Move
    return teams.TeamMove(Move.parse(left), int(point))


def certify(history: tuple[teams.TeamAction, ...], bound: int,
            *, unique: bool = False) -> dict:
    if type(bound) is not int or not 1 <= bound <= 9:
        raise ValueError("bound must be integer 1..9")
    state = teams.replay(history)
    if teams.winner(state) is not None:
        raise ValueError("terminal board is not a tactical puzzle")
    b = team_bitboard.TeamBits.from_state(state)
    fastgame, refgame = team_bitboard.BitboardFourPlayerGame(), teams.FourPlayerGame()
    fast, ref = ReferenceSolver(fastgame), ReferenceSolver(refgame)
    if fast.solve(b,bound) != Result.WIN or ref.solve(state,bound) != Result.WIN:
        raise ValueError("independent engines did not establish a forced team win")
    first_moves = tuple(m for m in teams.legal_moves(state)
                        if ref.solve(teams.apply(state,m),bound-1) == Result.LOSS)
    optimized_moves = tuple(m for m in team_bitboard.legal_moves(b)
                            if fast.solve(team_bitboard.apply(b,m),bound-1) == Result.LOSS)
    if not first_moves or set(first_moves) != set(optimized_moves):
        raise ValueError("solver disagrees on winning move set")
    if unique and len(first_moves) != 1:
        raise ValueError("not a unique win")
    horizon_values = [(d,ref.solve(state,d),fast.solve(b,d)) for d in range(1,bound+1)]
    if any(r != f for _,r,f in horizon_values):
        raise ValueError("four-player solvers disagree about shorter horizons")
    minimal = next(d for d,r,f in horizon_values if r == Result.WIN)
    proof = generic_proof.produce(fastgame,b,bound,fast)
    if generic_proof.verify(refgame,state,bound,proof) != Result.WIN:
        raise ValueError("independent four-player proof verifier rejected certificate")
    return {"schema": 1, "variant": "four-player", "history": [str(m) for m in history],
            "depth": bound, "unique": unique, "solutions": [str(m) for m in first_moves],
            "minimal_bound": minimal, "proof": proof}


def check(path: Path) -> dict:
    doc=json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != 1 or doc.get("variant") != "four-player":
        raise ValueError("expected four-player schema-1 certificate")
    saved = certify(tuple(parse_action(a) for a in doc["history"]), doc["depth"], unique=doc["unique"])
    if any(doc.get(k) != saved[k] for k in ("variant", "solutions", "minimal_bound", "proof")):
        raise ValueError("team tactical certificate does not match independent computation")
    return {"file":str(path), "result":"VERIFIED", "depth":doc["depth"],
            "minimal_bound":doc["minimal_bound"], "solutions": doc["solutions"]}


def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("files", nargs="*",type=Path)
    args=ap.parse_args(argv)
    files=args.files or sorted(Path("examples").glob("team_*.json"))
    if not files:
        ap.error("no four-player proof fixtures found")
    for file in files:
        print(json.dumps(check(file), sort_keys=True))


if __name__ == "__main__":
    main()
