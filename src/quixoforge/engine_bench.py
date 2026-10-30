"""Semantically fair fixed-depth alpha-beta vs independent exhaustive minimax.

The two methods evaluate the same heuristic objective at the same depth.
Measurements are local exploratory timings, not a global speed or strength claim.
"""
from __future__ import annotations
import argparse
import json
import platform
import statistics
import sys
import time
from .bench import positions
from . import reference
from .bitboard import Bits
from .engine import AlphaBetaEngine, MATE


def baseline(state, depth: int, stats: list[int]) -> int:
    stats[0] += 1
    w = reference.winner(state)
    if w is not None:
        return (MATE + depth) if w == state.turn else -(MATE + depth)
    moves = reference.legal_moves(state)
    if depth == 0 or not moves:
        return AlphaBetaEngine.evaluate(Bits.from_state(state))
    return max(-baseline(reference.apply(state, m), depth-1, stats) for m in moves)


def run(seed: int = 917, count: int = 6, plies: int = 14, depth: int = 2, repeats: int = 2) -> dict:
    if any(type(v) is not int for v in (seed, count, plies, depth, repeats)) or count <= 0 or plies < 0 or not 1 <= depth <= 3 or repeats < 1:
        raise ValueError("invalid benchmark settings; depth capped at 3 for exhaustive baseline")
    samples = positions(seed,count,plies)
    if not samples:
        raise ValueError("no nonterminal positions sampled")
    result = {"alpha_beta": {"elapsed_ns": [], "nodes": []},
              "independent_brute": {"elapsed_ns": [], "nodes": []}}
    for _ in range(repeats):
        for s in samples:
            eng = AlphaBetaEngine()
            t = time.perf_counter_ns()
            a = eng.recommend(s,depth=depth)
            dt = time.perf_counter_ns()-t
            result["alpha_beta"]["elapsed_ns"].append(dt)
            result["alpha_beta"]["nodes"].append(a.nodes)
            n=[0]
            t=time.perf_counter_ns()
            b=baseline(s,depth,n)
            dt=time.perf_counter_ns()-t
            result["independent_brute"]["elapsed_ns"].append(dt)
            result["independent_brute"]["nodes"].append(n[0])
            if a.aborted or a.completed_depth != depth or a.score != b:
                raise AssertionError("semantic mismatch: abort benchmark")
    return {"schema": 1, "seed": seed, "samples": len(samples), "plies": plies,
            "depth": depth, "repeats": repeats, "python": sys.version.split()[0],
            "platform": platform.platform(),
            "implementations": {k: {"median_elapsed_ns": statistics.median(v["elapsed_ns"]),
                                    "min_elapsed_ns": min(v["elapsed_ns"]),
                                    "max_elapsed_ns": max(v["elapsed_ns"]),
                                    "median_nodes": statistics.median(v["nodes"])}
                                for k,v in result.items()},
            "scope": "identical fixed-depth heuristic objective; local timings only"}


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed",type=int,default=917)
    ap.add_argument("--count",type=int,default=6)
    ap.add_argument("--plies",type=int,default=14)
    ap.add_argument("--depth",type=int,default=2)
    ap.add_argument("--repeats",type=int,default=2)
    print(json.dumps(run(**vars(ap.parse_args(argv))),sort_keys=True,indent=2))


if __name__ == "__main__":
    main()
