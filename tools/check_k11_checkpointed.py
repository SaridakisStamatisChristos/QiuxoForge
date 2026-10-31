"""Independent evidence gate for a checkpointed K11 partial census.

A completed occupancy-11 barrier is a meaningful exact finite-domain
observation. It is NOT an independent full K11 re-enumeration, and is
never converted into a purported complete all-25 puzzle count.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

K10_PINNED = {
    "raw_states": 6_375_326_636,
    "orbits": 797_089_672,
    "terminal_raw": 17_965_036,
    "win1_orbits": 26_504_343,
}
TOTAL10 = {
    "raw_states": 8_905_915_009,
    "orbits": 1_113_552_661,
    "terminal_raw": 20_729_244,
    "win1_orbits": 31_939_126,
}

def rows(path:Path):
    docs = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if any("cap" in row for row in docs):
        raise ValueError("partial streams must not claim completed-census footer")
    for i,row in enumerate(docs):
        if row.get("occupancy") != i or any(
            type(row.get(key)) is not int or row[key] < 0
            for key in K10_PINNED
        ):
            raise ValueError("missing/invalid occupancy record")
    return docs

def manifest(path:Path):
    fields=(path/"manifest.txt").read_text().splitlines()[0].split()
    if len(fields)!=9 or fields[:3]!=["QFCKPT1","5","12"]:
        raise ValueError("unexpected manifest schema/cap")
    next_k=int(fields[3])
    if next_k not in (11,12):
        raise ValueError("unexpected checkpoint level")
    vals=list(map(int,fields[4:]))
    return next_k,dict(zip(("raw_states","orbits","terminal_raw","win1_orbits","unique_win1_orbits"),vals))

def verify(prefix:Path,first_ckpt:Path,k11:Path|None=None,next_ckpt:Path|None=None):
    a=rows(prefix)
    if len(a)!=11 or a[-1]["occupancy"]!=10:
        raise ValueError("K10 frontier must contain exactly occupancies 0..10")
    if any(a[10][field]!=value for field,value in K10_PINNED.items()):
        raise ValueError("latest K10 occupancy differs from independently pinned result")
    for key,value in TOTAL10.items():
        if sum(row[key] for row in a)!=value:
            raise ValueError(f"K10 aggregate mismatch for {key}")
    if manifest(first_ckpt)!=(11,{**TOTAL10,"unique_win1_orbits":11_527_844}):
        raise ValueError("K10-frontier cumulative checkpoint mismatch")
    if k11 is None:
        return {"status":"PASS","complete_occupancy":10,"K11":"not_executed"}
    b=rows(k11)
    if len(b)!=1 or b[0]["occupancy"]!=11:
        # resumed partial output starts with its own occupied layer number,
        # so parse without relying on zero-based consecutive numbering.
        raise ValueError("K11 continuation must contain only occupancy 11")
    if next_ckpt is None:
        raise ValueError("no K12 next-frontier checkpoint after K11")
    next_k,agg=manifest(next_ckpt)
    if next_k!=12:
        raise ValueError("K11 did not produce next occupancy-12 frontier")
    for key in TOTAL10:
        if agg[key] != TOTAL10[key]+b[0][key]:
            raise ValueError(f"K11 checkpoint aggregate {key} differs from transcript")
    if not 11_527_844<=agg["unique_win1_orbits"]<=agg["win1_orbits"]:
        raise ValueError("invalid K11 unique winning root count")
    return {
        "status":"PASS",
        "complete_occupancy":11,
        "K11_one_engine_independence":"independent cross-enumeration still required",
        "K11":b[0],
        "cumulative":agg,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prefix",type=Path,required=True)
    p.add_argument("--checkpoint11",type=Path,required=True)
    p.add_argument("--k11",type=Path)
    p.add_argument("--checkpoint12",type=Path)
    a=p.parse_args()
    # The resumed K11 transcript starts at occupancy 11, so its fields
    # are checked separately from the prefix numbering.
    if a.k11 is not None:
        output=json.loads(a.k11.read_text().strip())
        if output.get("occupancy")!=11:
            raise ValueError("resume output does not describe K11")
        import tempfile
        first=verify(a.prefix,a.checkpoint11)
        assert first["status"]=="PASS"
        if a.checkpoint12 is None:
            raise ValueError("missing checkpoint-12")
        next_k,agg=manifest(a.checkpoint12)
        if next_k!=12:raise ValueError("missing complete K12 frontier")
        for key in TOTAL10:
            if agg[key] != TOTAL10[key]+output[key]:
                raise ValueError(f"K11 cumulative mismatch {key}")
        if not 11_527_844<=agg["unique_win1_orbits"]<=agg["win1_orbits"]:
            raise ValueError("K11 unique-win count invalid")
        print(json.dumps({
            "status":"PASS","scope":"single-engine exact checkpointed K11 census, independent K11 enumeration pending",
            "K11":output,"cumulative":agg,
        },sort_keys=True))
    else:
        print(json.dumps(verify(a.prefix,a.checkpoint11),sort_keys=True))

if __name__=="__main__":
    main()
