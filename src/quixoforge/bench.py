"""Semantics-first reproducible search benchmark, no performance assertions."""
from __future__ import annotations
import argparse
import json
import platform
import random
import statistics
import sys
import time
from .model import initial, State
from .reference import legal_moves, apply, winner
from .solver import ReferenceSolver, BitboardSolver


def positions(seed: int, count: int, plies: int) -> list[State]:
    rng = random.Random(seed)
    samples = []
    for _ in range(count):
        s = initial()
        for _ in range(plies):
            moves = legal_moves(s)
            if not moves:
                break
            s = apply(s, rng.choice(moves))
        if winner(s) is None and legal_moves(s):
            samples.append(s)
    return samples


def run(seed: int = 711, count: int = 8, plies: int = 9, depth: int = 2,
        repeats: int = 3) -> dict:
    if min(count, plies, repeats, depth) < 0 or repeats < 1 or count < 1:
        raise ValueError("invalid benchmark parameters")
    samples = positions(seed, count, plies)
    if not samples:
        raise ValueError("no suitable reachable nonterminal benchmark positions")
    times = {"reference": [], "bitboard": []}
    nodes = {"reference": [], "bitboard": []}
    # both implementations run on the identical sequence of replayed positions
    for _ in range(repeats):
        for s in samples:
            outcomes = []
            for name, cls in (("reference", ReferenceSolver), ("bitboard", BitboardSolver)):
                solver = cls()
                t0 = time.perf_counter_ns()
                result = solver.solve(s, depth)
                ns = time.perf_counter_ns()-t0
                times[name].append(ns)
                nodes[name].append(solver.stats.nodes)
                outcomes.append(result)
            if outcomes[0] != outcomes[1]:
                raise AssertionError("benchmark aborted: unequal semantics")
    return {"schema": 1, "seed": seed, "requested_count": count,
            "samples": len(samples), "plies": plies, "depth": depth, "repeats": repeats,
            "python": sys.version.split()[0], "platform": platform.platform(),
            "implementations": {name: {"median_ns": statistics.median(t),
                         "min_ns": min(t), "max_ns": max(t),
                         "median_search_nodes": statistics.median(nodes[name])}
                      for name, t in times.items()},
            "scope": "local wall-clock exploratory; no cross-platform speed claim"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=711)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--plies", type=int, default=9)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args(argv)
    print(json.dumps(run(**vars(args)), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
