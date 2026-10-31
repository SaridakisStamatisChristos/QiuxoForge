"""External, independent evidence gate for tier-bitset 5x5 exact census.

Uses fixed outputs previously reproduced by both the native whole-graph D4
queue and an independently coded, unsymmetrized rank-bitset raw-state BFS.
Never upgrades a partial census to an all-25-occupancy conclusion.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

KNOWN = [
    (1, 1, 0, 0),
    (16, 3, 0, 0),
    (468, 60, 0, 0),
    (11812, 1512, 0, 0),
    (187164, 23659, 0, 0),
    (2055382, 258081, 0, 120),
    (16353436, 2048650, 552, 3674),
    (99693740, 12475164, 15748, 60180),
    (484731202, 60627546, 247248, 634614),
    (1927555152, 241028313, 2500660, 4736195),
]

def check(path: str | Path) -> dict:
    records = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if not records or "cap" not in records[-1]:
        raise ValueError("missing complete end-of-run summary; partial runs are invalid")
    final = records[-1]
    cap = final["cap"]
    if type(cap) is not int or not 0 <= cap <= 25:
        raise ValueError("invalid cap")
    if len(records) != cap + 2:
        raise ValueError("missing/duplicate occupancy-level results")
    for k, record in enumerate(records[:-1]):
        if record.get("occupancy") != k:
            raise ValueError("occupancy levels not consecutive")
        for field in ("raw_states", "orbits", "terminal_raw", "win1_orbits"):
            if type(record.get(field)) is not int or record[field] < 0:
                raise ValueError(f"missing or invalid {field} at occupancy {k}")
        if k < len(KNOWN):
            got = tuple(record[field] for field in (
                "raw_states", "orbits", "terminal_raw", "win1_orbits"))
            if got != KNOWN[k]:
                raise ValueError(f"independent pinned-count mismatch for {k}: {got}")
        if record["orbits"] > record["raw_states"]:
            raise ValueError("orbits cannot exceed raw states")
    for field, src in [
        ("total_raw", "raw_states"),
        ("total_orbits", "orbits"),
        ("total_terminal_raw", "terminal_raw"),
        ("total_win1_orbits", "win1_orbits"),
    ]:
        if final[field] != sum(item[src] for item in records[:-1]):
            raise ValueError(f"aggregate mismatch: {field}")
    if final["total_unique_win1_orbits"] > final["total_win1_orbits"]:
        raise ValueError("unique winning roots exceed winning roots")
    if cap >= 8:
        assert sum(r["orbits"] for r in records[:9]) == 75_434_676
        assert sum(r["raw_states"] for r in records[:9]) == 603_033_221
    if cap >= 9:
        if sum(r["orbits"] for r in records[:10]) != 316_462_989:
            raise ValueError("new exact K9 D4 census mismatch")
        if sum(r["raw_states"] for r in records[:10]) != 2_530_588_373:
            raise ValueError("new exact K9 raw-state census mismatch")
        if sum(r["win1_orbits"] for r in records[:10]) != 5_434_783:
            raise ValueError("new exact K9 winning-root census mismatch")
    if cap == 9 and final["total_unique_win1_orbits"] != 1_942_916:
        raise ValueError("new exact unique-win1 K9 total mismatch")
    return final

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    args = ap.parse_args()
    result = check(args.jsonl)
    print(json.dumps({"verification": "PASS", "final": result}, sort_keys=True))

if __name__ == "__main__":
    main()
