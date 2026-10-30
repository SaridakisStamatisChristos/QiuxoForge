"""Standalone, reproducible proof audit for committed tactical examples."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .model import Move
from .puzzles import Puzzle, audit
from .proof import verify
from .solver import Result


def check(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != 1:
        raise ValueError(f"unsupported example schema: {path}")
    puzzle = Puzzle(tuple(Move.parse(s) for s in doc["history"]), doc["depth"])
    report = audit(puzzle, require_unique=doc["unique"])
    if [str(m) for m in report.solutions] != doc["solutions"]:
        raise ValueError(f"solution set changed: {path}")
    if "minimal_bound" in doc and doc["minimal_bound"] != report.minimal_bound:
        raise ValueError(f"false minimal horizon metadata: {path}")
    if "difficulty" in doc and doc["difficulty"] != report.difficulty:
        raise ValueError(f"false difficulty metadata: {path}")
    if verify(puzzle.state(), doc["depth"], doc["proof"]) != Result.WIN:
        raise ValueError(f"invalid certificate: {path}")
    return {"file": str(path), "result": "VERIFIED", "minimal_bound": report.minimal_bound,
            "solutions": doc["solutions"], "reference_nodes": report.reference_nodes,
            "bitboard_nodes": report.bitboard_nodes}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", type=Path)
    args = ap.parse_args(argv)
    files = args.files or sorted(p for p in Path("examples").glob("*.json") if not p.name.startswith("team_"))
    if not files:
        ap.error("no examples provided or discovered; run from repository root")
    for path in files:
        print(json.dumps(check(path), sort_keys=True))

if __name__ == "__main__":
    main()
