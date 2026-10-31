"""Proof-gated, D4-deduplicated playable 5x5 Quixo puzzle bank.

This builds a bank of verified puzzles, not a claimed full-game catalogue.
A position is published only after:
  1. a legal X-first replay from the empty board,
  2. both bounded solvers agree on the complete winning first-action set,
  3. an independent AND/OR certificate verifies against every defense,
  4. minimum forced winning horizon (and optional unique first action) matches,
  5. its (board,turn) D4 orbit is absent from the bank.
"""
from __future__ import annotations

from hashlib import sha256
import json
import random
from typing import Any

from .generator import generate
from .model import Move, replay, X, O
from .puzzles import Puzzle, audit
from .proof import verify
from .reference import winner
from .solver import Result
from .symmetry import canonical


def _valid_int(value: object, lower: int, upper: int, name: str) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in {lower}..{upper}")
    return value


def _identity(state) -> str:
    """Canonical stable identifier, retaining colors and side-to-move."""
    turn, cells = canonical(state)
    payload = bytes([turn + 1]) + cells
    return sha256(payload).hexdigest()


def _board(state) -> str:
    return "".join("." if v == 0 else "X" if v == X else "O" for v in state.cells)


def verify_entry(entry: dict[str, Any], *, exact_horizon: bool = True,
                 unique: bool = True) -> str:
    """Reaudit one supplied puzzle, failing closed on any tampering.

    Returns its D4-orbit identifier. No API ever assumes a board array is
    reachable merely because its markings look plausible.
    """
    if type(entry) is not dict or entry.get("schema") != 1:
        raise ValueError("invalid puzzle document")
    history = entry.get("history")
    if type(history) is not list or not all(type(t) is str for t in history):
        raise ValueError("invalid replay history")
    try:
        moves = tuple(Move.parse(text) for text in history)
        state = replay(moves)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError("puzzle history is not legally replayable") from e
    if winner(state) is not None:
        raise ValueError("already-terminal board cannot be a puzzle")
    bound = _valid_int(entry.get("depth"), 1, 9, "depth")
    if type(entry.get("unique")) is not bool or entry["unique"] != unique:
        raise ValueError("uniqueness contract mismatch")
    report = audit(Puzzle(moves, bound), require_unique=unique)
    if report.minimal_bound != entry.get("minimal_bound"):
        raise ValueError("claimed minimum forced-winning horizon is false")
    if exact_horizon and report.minimal_bound != bound:
        raise ValueError("puzzle was solvable in fewer plies")
    if entry.get("solutions") != [str(m) for m in report.solutions]:
        raise ValueError("claimed solution set differs from independent solvers")
    if verify(state, bound, entry.get("proof")) != Result.WIN:
        raise ValueError("winning certificate does not cover every defense")
    orbit_id = _identity(state)
    if entry.get("orbit_id") != orbit_id:
        raise ValueError("claimed geometric orbit identifier differs")
    if entry.get("board") != _board(state):
        raise ValueError("claimed board differs from the legal replay")
    if entry.get("turn") != ("X" if state.turn == X else "O"):
        raise ValueError("claimed player-to-move differs")
    return orbit_id


def generate_bank(*, count: int, seed: int, depth: int = 1,
                  unique: bool = True, exact_horizon: bool = True,
                  searches: int = 100, attempts_per_search: int = 100,
                  min_plies: int = 8, max_plies: int = 32) -> dict:
    """Generate exactly count fully checked, D4-distinct 5x5 puzzles or fail.

    All searches are bounded. Raising LookupError is an honest *failure to
    find* in this search budget, never a proof of absence. Deterministic
    for fixed arguments and package version; no external APIs or AI model.
    """
    _valid_int(count, 1, 10000, "count")
    _valid_int(seed, -2**63, 2**63-1, "seed")
    _valid_int(depth, 1, 9, "depth")
    _valid_int(searches, 1, 1000000, "searches")
    _valid_int(attempts_per_search, 1, 1000000, "attempts_per_search")
    _valid_int(min_plies, 0, 100000, "min_plies")
    _valid_int(max_plies, min_plies, 100000, "max_plies")
    if type(unique) is not bool or type(exact_horizon) is not bool:
        raise ValueError("unique and exact_horizon must be booleans")

    rng = random.Random(seed)
    records: list[dict] = []
    seen: set[str] = set()
    for attempt in range(searches):
        trial_seed = rng.getrandbits(63)
        try:
            doc = generate(seed=trial_seed, bound=depth,
                           attempts=attempts_per_search,
                           min_plies=min_plies, max_plies=max_plies,
                           unique=unique)
        except LookupError:
            continue
        if exact_horizon and doc["minimal_bound"] != depth:
            continue
        state = replay(tuple(Move.parse(m) for m in doc["history"]))
        orbit = _identity(state)
        if orbit in seen:
            continue
        doc = {**doc, "orbit_id": orbit, "board": _board(state),
               "turn": "X" if state.turn == X else "O"}
        verify_entry(doc, exact_horizon=exact_horizon, unique=unique)
        seen.add(orbit)
        records.append(doc)
        if len(records) == count:
            bank = {
                "schema": 1,
                "variant": "5x5_two_player_X_first",
                "equivalence": "D4_geometry_only; preserve_colors_and_turn",
                "objective": "forced_win_within_plies",
                "depth": depth,
                "unique": unique,
                "exact_horizon": exact_horizon,
                "requested": count,
                "generated": count,
                "generation": {
                    "seed": seed, "searches_budget": searches,
                    "attempts_per_search": attempts_per_search,
                    "min_plies": min_plies, "max_plies": max_plies,
                    "searches_used": attempt + 1,
                },
                "puzzles": records,
            }
            verify_bank(bank)
            return bank
    raise LookupError(f"only {len(records)} of {count} certified D4-distinct "
                      f"puzzles found within {searches} seeded searches; "
                      "nothing published as a complete requested bank")


def verify_bank(bank: dict) -> int:
    """Independently recheck all entries, quotas and non-duplicated D4 orbits."""
    if type(bank) is not dict or bank.get("schema") != 1:
        raise ValueError("invalid bank schema")
    if bank.get("variant") != "5x5_two_player_X_first" or bank.get("equivalence") != (
        "D4_geometry_only; preserve_colors_and_turn"
    ) or bank.get("objective") != "forced_win_within_plies":
        raise ValueError("bank game or identity contract mismatch")
    count = _valid_int(bank.get("requested"), 1, 10000, "requested")
    puzzles = bank.get("puzzles")
    if type(puzzles) is not list or len(puzzles) != count or bank.get("generated") != count:
        raise ValueError("bank count is incomplete or inconsistent")
    depth = _valid_int(bank.get("depth"), 1, 9, "depth")
    unique, exact = bank.get("unique"), bank.get("exact_horizon")
    if type(unique) is not bool or type(exact) is not bool:
        raise ValueError("invalid unique/exact horizon flags")
    distinct: set[str] = set()
    for doc in puzzles:
        if doc.get("depth") != depth:
            raise ValueError("mixed puzzle horizons")
        key = verify_entry(doc, exact_horizon=exact, unique=unique)
        if key in distinct:
            raise ValueError("duplicate puzzle under D4 board geometry")
        distinct.add(key)
    return count


def bank_json(bank: dict) -> str:
    """Stable JSON encoding for portable, replayable puzzle banks."""
    verify_bank(bank)
    return json.dumps(bank, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
