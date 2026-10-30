"""Independent output-contract validator for the native 5x5 census experiments.

All values are fixed empirical reference outputs from separate local runs.
This checker does not implement the native graph search.
"""
from __future__ import annotations
import argparse
import json
from math import comb
from pathlib import Path
from structural_orbit_bounds import coefficient

REFERENCE = {
    5: {
        "reachable_states": 2254843, "d4_orbits": 283316,
        "terminal_states": 0, "terminal_orbits": 0,
        "win_in_one_states": 936, "win_in_one_orbits": 120,
        "unique_win_in_one_states": 360, "unique_win_in_one_orbits": 46,
        "candidate_edges_repr": 11081205, "retained_edges_repr": 2232992,
    },
    6: {
        "reachable_states": 18608279, "d4_orbits": 2331966,
        "terminal_states": 552, "terminal_orbits": 80,
        "win_in_one_states": 30076, "win_in_one_orbits": 3794,
        "unique_win_in_one_states": 9868, "unique_win_in_one_orbits": 1248,
        "candidate_edges_repr": 89470258, "retained_edges_repr": 22384725,
    },
    7: {
        "reachable_states": 118302019, "d4_orbits": 14807130,
        "terminal_states": 16300, "terminal_orbits": 2150,
        "win_in_one_states": 510500, "win_in_one_orbits": 63974,
        "unique_win_in_one_states": 171788, "unique_win_in_one_orbits": 21531,
        "candidate_edges_repr": 556930564, "retained_edges_repr": 168094825,
    },
    8: {
        "reachable_states": 603033221, "d4_orbits": 75434676,
        "terminal_states": 263548, "terminal_orbits": 33441,
        "win_in_one_states": 5581768, "win_in_one_orbits": 698588,
        "unique_win_in_one_states": 1948992, "unique_win_in_one_orbits": 243957,
        "candidate_edges_repr": 2779496257, "retained_edges_repr": 988048999,
    },
}
LAYER = {
    0: (1, 1, 0, 0, 0, 0, 0, 0),
    1: (16, 3, 0, 0, 0, 0, 0, 0),
    2: (468, 60, 0, 0, 0, 0, 0, 0),
    3: (11812, 1512, 0, 0, 0, 0, 0, 0),
    4: (187164, 23659, 0, 0, 0, 0, 0, 0),
    5: (2055382, 258081, 0, 0, 936, 120, 360, 46),
    6: (16353436, 2048650, 552, 80, 29140, 3674, 9508, 1202),
    7: (99693740, 12475164, 15748, 2070, 480424, 60180, 161920, 20283),
    8: (484731202, 60627546, 247248, 31291, 5071268, 634614, 1777204, 222426),
}
KEYS = (
    "reachable_states", "d4_orbits", "terminal_states", "terminal_orbits",
    "win_in_one_states", "win_in_one_orbits",
    "unique_win_in_one_states", "unique_win_in_one_orbits",
)


def validate_native(doc: dict, cap: int) -> None:
    if doc.get("schema") != 1 or doc.get("cap") != cap:
        raise AssertionError("invalid schema or occupancy scope")
    for key, expected in REFERENCE[cap].items():
        if doc.get(key) != expected:
            raise AssertionError(f"{key}: {doc.get(key)} != {expected}")
    rows = doc["occupancies"]
    if len(rows) != cap + 1:
        raise AssertionError("missing occupancy stratum")
    for index, row in enumerate(rows):
        if row["k"] != index:
            raise AssertionError("misordered occupancy strata")
        for field, expected in zip(KEYS, LAYER[index]):
            if row[field] != expected:
                raise AssertionError(f"k={index}, {field}: {row[field]} != {expected}")
        if row["terminal_states"] + row["win_in_one_states"] > row["reachable_states"]:
            raise AssertionError("terminal root cannot be a tactical root")
        if row["unique_win_in_one_orbits"] > row["win_in_one_orbits"]:
            raise AssertionError("unique objective is not a subset")
        if row["reachable_states"] > 2 * comb(25, index) * (2 ** index):
            raise AssertionError("raw state exceeds structural upper bound")
        if row["d4_orbits"] > coefficient(index):
            raise AssertionError("reachability D4 classes exceed proved Burnside upper bound")
    for field in KEYS:
        if doc[field] != sum(row[field] for row in rows):
            raise AssertionError(f"non-additive total: {field}")
    hist = doc["orbit_sizes"]
    if sum(int(k) * v for k, v in hist.items()) != doc["reachable_states"]:
        raise AssertionError("Burnside orbit-size partition mismatch")
    if sum(hist.values()) != doc["d4_orbits"]:
        raise AssertionError("missing D4 orbits")


def validate_raw(doc: dict) -> None:
    if doc["cap"] != 6 or doc["raw_states"] != REFERENCE[6]["reachable_states"]:
        raise AssertionError("raw 6-cube count mismatch")
    if doc["by_occupancy"] != [LAYER[k][0] for k in range(7)]:
        raise AssertionError("raw layers mismatch")
    if doc["terminal_by_occupancy"] != [LAYER[k][2] for k in range(7)]:
        raise AssertionError("independent terminal layer mismatch")
    if doc["candidate_edges"] != 713951292 or doc["retained_edges"] != 178424208:
        raise AssertionError("independent directed-edge totals mismatch")



def validate_raw7(doc: dict) -> None:
    """Independent unsymmetrized 118M-state enumeration, including negatives."""
    if doc.get("schema") != 1 or doc.get("cap") != 7:
        raise AssertionError("independent seven-cube scope mismatch")
    if doc["raw_states"] != REFERENCE[7]["reachable_states"]:
        raise AssertionError("independent seven-cube raw count mismatch")
    if doc["by_occupancy"] != [LAYER[k][0] for k in range(8)]:
        raise AssertionError("independent seven-cube occupancy breakdown mismatch")
    if doc["terminal_by_occupancy"] != [LAYER[k][2] for k in range(8)]:
        raise AssertionError("independent seven-cube terminal outcomes mismatch")
    if doc["win_in_one_by_occupancy"] != [LAYER[k][4] for k in range(8)]:
        raise AssertionError("independent full-scope first-action wins mismatch")
    if doc["unique_win_in_one_by_occupancy"] != [LAYER[k][6] for k in range(8)]:
        raise AssertionError("independent full-scope unique-action wins mismatch")
    if doc["candidate_edges"] != 4449658784 or doc["retained_edges"] != 1342280992:
        raise AssertionError("independent full-scope edge totals mismatch")


def validate_raw8(doc: dict) -> None:
    """Independent compressed-rank 603M-state reachability and full tactical oracle."""
    if doc.get("schema") != 1 or doc.get("cap") != 8:
        raise AssertionError("independent eight-cube scope mismatch")
    if doc["raw_states"] != REFERENCE[8]["reachable_states"]:
        raise AssertionError("independent eight-cube raw reachability mismatch")
    if doc["by_occupancy"] != [LAYER[k][0] for k in range(9)]:
        raise AssertionError("independent eight-cube occupancy layers disagree")
    if doc["terminal_by_occupancy"] != [LAYER[k][2] for k in range(9)]:
        raise AssertionError("independent eight-cube terminal states disagree")
    if doc["win_in_one_by_occupancy"] != [LAYER[k][4] for k in range(9)]:
        raise AssertionError("independent eight-cube winning-action positions disagree")
    if doc["unique_win_in_one_by_occupancy"] != [LAYER[k][6] for k in range(9)]:
        raise AssertionError("independent eight-cube unique-action positions disagree")
    if doc["structural_bits"] != 703338822:
        raise AssertionError("dense combinatorial rank domain mismatch")


def validate_forced3(native: dict, oracle: dict) -> None:
    if native.get("schema") != 1 or native.get("cap") != 7:
        raise AssertionError("three-ply native cap/schema mismatch")
    values = {
        "new_exactly_three_orbits": 370,
        "new_exactly_three_raw": 2880,
        "unique_exactly_three_orbits": 64,
        "unique_exactly_three_raw": 512,
    }
    for name, value in values.items():
        if native.get(name) != value:
            raise AssertionError(f"three-ply count mismatch {name}")
    if oracle.get("exactly_three_orbits") != 370 or oracle.get("raw_state_weight") != 2880:
        raise AssertionError("independent positive proof count disagrees")
    if oracle.get("unique_forcing_first_action_orbits") != 64:
        raise AssertionError("independent unique-first-action count disagrees")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Evidence-check native full-board Quixo outputs")
    parser.add_argument("--k5", type=Path, required=True)
    parser.add_argument("--k6", type=Path, required=True)
    parser.add_argument("--k7", type=Path, required=True)
    parser.add_argument("--k8", type=Path, required=True)
    parser.add_argument("--raw6", type=Path, required=True)
    parser.add_argument("--raw7", type=Path, required=True)
    parser.add_argument("--raw8", type=Path, required=True)
    parser.add_argument("--f3", type=Path, required=True)
    parser.add_argument("--f3-certified", type=Path, required=True)
    args = parser.parse_args(argv)
    for cap, file in ((5, args.k5), (6, args.k6), (7, args.k7), (8, args.k8)):
        validate_native(json.loads(file.read_text(encoding="utf8")), cap)
    validate_raw(json.loads(args.raw6.read_text(encoding="utf8")))
    validate_raw7(json.loads(args.raw7.read_text(encoding="utf8")))
    validate_raw8(json.loads(args.raw8.read_text(encoding="utf8")))
    validate_forced3(json.loads(args.f3.read_text(encoding="utf8")),
                     json.loads(args.f3_certified.read_text(encoding="utf8")))
    print("PASS: native 5x5 K5-K8 families, D4 partitions, raw K6 and raw K7 independent BFS plus tactical negatives")


if __name__ == "__main__":
    main()
