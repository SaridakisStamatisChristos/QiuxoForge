"""Compare independent old in-memory and new out-of-core exact 5x5 censuses.

Explicitly ignore resource/timing diagnostic fields; every occupancy's
actual board-position and tactic counts must agree *exactly*.
Do not treat a truncated JSONL trace as a successful census.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CORE = ("occupancy", "raw_states", "orbits", "terminal_raw", "win1_orbits")
TOTAL = ("cap", "total_raw", "total_orbits", "total_terminal_raw",
         "total_win1_orbits", "total_unique_win1_orbits")

def read_result(path: Path):
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]
    if not rows or "cap" not in rows[-1]:
        raise ValueError("truncated or absent complete census summary")
    cap = rows[-1]["cap"]
    if type(cap) is not int or cap < 0 or len(rows) != cap + 2:
        raise ValueError("wrong number of occupancy records")
    if any(row.get("occupancy") != k for k,row in enumerate(rows[:-1])):
        raise ValueError("missing/repeated/reordered occupancy")
    return rows

def compare(a: Path, b: Path):
    left,right=read_result(a),read_result(b)
    for i,(x,y) in enumerate(zip(left[:-1],right[:-1])):
        for field in CORE:
            if x.get(field) != y.get(field):
                raise ValueError(
                    f"K={i} {field} differs: oracle={x.get(field)} external={y.get(field)}")
    if len(left)!=len(right):
        raise ValueError("different occupancy range")
    for field in TOTAL:
        if left[-1].get(field)!=right[-1].get(field):
            raise ValueError(f"aggregate {field} differs")
    return {field:right[-1][field] for field in TOTAL}

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: check_external_equivalence.py oracle.jsonl external.jsonl")
    out=compare(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps({"status":"PASS","comparison":"all occupancy rows and aggregate counts","result":out},sort_keys=True))
