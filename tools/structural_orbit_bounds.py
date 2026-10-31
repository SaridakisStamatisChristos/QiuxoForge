"""Provably exact D4 structural orbit counts for every occupancy K=0..25.

NO reachability or winner assumption. An independent mathematical ceiling
on any exact reachable Quixo puzzle census, retaining X/O and turn.
"""
from __future__ import annotations

import argparse
from math import comb
import json

def coefficient(k: int) -> int:
    """Two-turn D4 orbit count of all 25-cell 3-color boards with K marks."""
    if type(k) is not int or not 0 <= k <= 25:
        raise ValueError("occupancy must be a genuine integer in 0..25")
    identity = comb(25, k) * 2**k
    quarter = sum(
        2**a * comb(6, b) * 2**b
        for a in (0, 1) for b in range(7) if a + 4 * b == k
    )
    half = sum(
        2**a * comb(12, b) * 2**b
        for a in (0, 1) for b in range(13) if a + 2 * b == k
    )
    reflection = sum(
        comb(5, a) * 2**a * comb(10, b) * 2**b
        for a in range(6) for b in range(11) if a + 2*b == k
    )
    incidence = identity + 2*quarter + half + 4*reflection
    if incidence % 4:
        raise AssertionError("nonintegral D4 Burnside result")
    return incidence // 4

def all_coefficients() -> dict:
    by_occupancy = {str(k): coefficient(k) for k in range(26)}
    total = sum(by_occupancy.values())
    if total != 211836900942:
        raise AssertionError("full 3^25 Burnside sum disagrees")
    if coefficient(8) != 69278970:
        raise AssertionError("eight-cube Burnside coefficient discrepancy")
    return {
        "schema": 1,
        "domain": "ALL structural 5x5 3-color board/turn classes, D4, NOT reachable",
        "by_occupancy": by_occupancy,
        "total_structural_orbits": total,
        "formula": "B_k=[x^k]((1+2x)^25+2(1+2x)(1+2x^4)^6+(1+2x)(1+2x^2)^12+4(1+2x)^5(1+2x^2)^10)/4",
    }

def main(argv=None):
    p = argparse.ArgumentParser(description="Exact all-K structural Quixo D4 bounds")
    p.add_argument("--k", type=int)
    args = p.parse_args(argv)
    print(json.dumps(all_coefficients() if args.k is None else {
        "k": args.k, "structural_orbits": coefficient(args.k),
    }, sort_keys=True))

if __name__ == "__main__":
    main()
