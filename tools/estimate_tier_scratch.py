"""Deterministic structural scratch-capacity planner for 5x5 tier bitsets.

Provides exact upper bounds for bitmap and queue file *capacities*, NOT
predictions of actual reachable states, runtime, or unique puzzle counts.
"""
from __future__ import annotations
import argparse
import json
from math import comb

def tier_universe(x: int, o: int) -> int:
    if not (0 <= x <= 25 and 0 <= o <= 25 - x):
        raise ValueError("invalid mark counts")
    return 2 * comb(25, x) * comb(25 - x, o)

def layer_bitmap_bytes(k: int) -> int:
    if not 0 <= k <= 25:
        raise ValueError("occupancy must be 0..25")
    return sum(((tier_universe(x, k-x) + 63) // 64) * 8
               for x in range(k+1))

def capacity_plan(cap: int) -> dict:
    if type(cap) is not int or not 0 <= cap <= 25:
        raise ValueError("cap must be an integer from 0 to 25")
    rows=[]
    for k in range(cap+1):
        bitmap=layer_bitmap_bytes(k)
        following=layer_bitmap_bytes(k+1) if k < cap else 0
        largest_tier=max(tier_universe(x,k-x) for x in range(k+1))
        max_fifo=largest_tier*8
        rows.append({
            "occupancy": k,
            "bitmap_file_bytes_all_color_tiers": bitmap,
            "next_level_bitmap_file_bytes": following,
            "largest_tier_fifo_bytes_structural_upper_bound": max_fifo,
            "combined_scratch_bytes_conservative_upper_bound":
                bitmap+following+max_fifo,
        })
    return {
        "scope":"5x5 two-player two-color-and-turn rank-universe capacity upper bounds",
        "cap":cap,
        "upper_bound_not_memory_measurement":True,
        "fifo_buffer_ram_bytes": 2*32768*8,
        "largest_structural_scratch_upper_bound_bytes":
            max(row["combined_scratch_bytes_conservative_upper_bound"] for row in rows),
        "occupancies":rows,
        "warnings":[
            "Upper bounds include structurally unreachable states.",
            "Mapped pages can still reside in OS page cache: no fixed total RSS guarantee.",
            "Scratch shortages are fatal; full K25 census is not yet proven tractable.",
            "These numbers say nothing about game-theoretic WIN/LOSS/DRAW classification.",
        ]
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--cap",type=int,default=11)
    args=ap.parse_args()
    print(json.dumps(capacity_plan(args.cap),sort_keys=True))
