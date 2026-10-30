"""Portable verified 3x3 Quixo strong-solution tablebase (all reachable states).

The game is solved under the standard infinite-play-as-nonforced convention:
NONFORCED means neither side can force a terminal win. The published official
5x5 Quixo result is a draw; this included database applies ONLY to 3x3.

Data is generated exclusively by exhaustive independent retrograde traversal.
A SHA256-bound load rejects corruption or stale datasets. All positions have
been independently checked with separate reference and bitboard oracles.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from io import BytesIO
import gzip
import json
import struct
from types import MappingProxyType

from .model import Move, X, O
from .retrograde import Outcome, solve, verify
from .variants import VariantBits, VariantBitboard, VariantReference, VariantState, initial

MAGIC = b'QF3\x01'
RECORD = struct.Struct('<HHbBB')  # x, o, turn, outcome code, remoteness
HEADER = struct.Struct('<4sI')
EXPECTED_STATES = 32027  # From Shi 2024; independently recreated below.
# SHA-256 of packaged compressed content is fixed at build time; updated only
# after independently running both exhaustive rule models.
TABLEBASE_SHA256 = '6ad95cb58dd78e675bed99136ea73dbc9c1507a85bd198ef154640dabf015eae'
CODES = {Outcome.WIN: 1, Outcome.LOSS: 2, Outcome.NONFORCED: 3}
INVERSE_CODES = {v:k for k,v in CODES.items()}


@dataclass(frozen=True)
class Value:
    outcome: Outcome
    remoteness: int | None


def _key(state: VariantState | VariantBits) -> tuple[int, int, int]:
    b = VariantBits.from_state(state) if isinstance(state, VariantState) else state
    if not isinstance(b, VariantBits) or b.size != 3:
        raise ValueError('3x3 state required')
    return (b.x, b.o, b.turn)


def generate() -> tuple[bytes, dict]:
    """Regenerate whole table from TWO independent complete game graphs.

    This is a research build command, not required during normal lookup.
    All 32,027 states and the complete optimal remoteness array must agree.
    """
    ref = VariantReference(3)
    opt = VariantBitboard(3)
    a = solve(ref, initial(3), max_states=40_000)
    b = solve(opt, VariantBits.from_state(initial(3)), max_states=40_000)
    verify(ref, a)
    verify(opt, b)
    if len(a.outcomes) != EXPECTED_STATES or len(b.outcomes) != EXPECTED_STATES:
        raise AssertionError('published independent state count mismatch')
    if a.edge_count != b.edge_count:
        raise AssertionError('independent edge count mismatch')
    by_key = {_key(state): Value(out, a.remoteness.get(state)) for state,out in a.outcomes.items()}
    opt_key = {_key(state): Value(out, b.remoteness.get(state)) for state,out in b.outcomes.items()}
    if by_key != opt_key:
        wrong = next(k for k in by_key if by_key[k] != opt_key.get(k))
        raise AssertionError(f'independent game value disagreement at {wrong}')
    # Check full directed multigraph equality, not just summaries or values.
    for state, successors in a.successors.items():
        bitstate = VariantBits.from_state(state)
        if tuple(map(_key, successors)) != tuple(map(_key, b.successors[bitstate])):
            raise AssertionError('independent transition graph mismatch')
    raw = bytearray(HEADER.pack(MAGIC, len(by_key)))
    for (x,o,turn), value in sorted(by_key.items()):
        if value.remoteness is None:
            dist = 255
        else:
            dist = value.remoteness
            if not 0 <= dist < 255:
                raise AssertionError('remoteness exceeds portable encoding')
        raw.extend(RECORD.pack(x,o,turn,CODES[value.outcome],dist))
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, filename='', mode='wb', compresslevel=9, mtime=0) as compressed:
        compressed.write(raw)
    report = {'schema': 1, 'variant': 'two-player-3x3-three-in-row',
              'reachable_states': len(by_key), 'legal_transitions': a.edge_count,
              'initial_outcome': a.outcome(initial(3)).value,
              'initial_remoteness_plies': a.remoteness[initial(3)],
              'outcomes': {v.value: sum(x == v for x in a.outcomes.values()) for v in Outcome},
              'raw_sha256': sha256(raw).hexdigest(),
              'compressed_sha256': sha256(out.getvalue()).hexdigest(),
              'complete_reference_bitboard_agreement': True}
    return out.getvalue(), report


class Tablebase:
    """Immutable exact table for all reachable states, with optimal actions."""
    def __init__(self, payload: bytes, *, expected_sha: str = TABLEBASE_SHA256):
        if sha256(payload).hexdigest() != expected_sha:
            raise ValueError('tablebase checksum mismatch')
        try:
            raw = gzip.decompress(payload)
        except (ValueError, OSError) as exc:
            raise ValueError('corrupted compressed tablebase') from exc
        if len(raw) < HEADER.size:
            raise ValueError('missing tablebase header')
        magic, count = HEADER.unpack_from(raw)
        if magic != MAGIC or count != EXPECTED_STATES or len(raw) != HEADER.size + count*RECORD.size:
            raise ValueError('invalid tablebase format / state count')
        entries: dict[tuple[int,int,int], Value] = {}
        for offset in range(HEADER.size,len(raw),RECORD.size):
            x,o,turn,code,rem = RECORD.unpack_from(raw,offset)
            key = (x,o,turn)
            if key in entries or code not in INVERSE_CODES:
                raise ValueError('invalid or duplicate tablebase row')
            VariantBits(x,o,turn,3)  # structural validation, including overlap
            if (code == 3) != (rem == 255):
                raise ValueError('invalid remoteness format')
            entries[key] = Value(INVERSE_CODES[code], None if rem == 255 else rem)
        self._entries = MappingProxyType(entries)

    @classmethod
    def load(cls) -> 'Tablebase':
        payload = files('quixoforge').joinpath('data/quixo3.tbl.gz').read_bytes()
        return cls(payload)

    @property
    def states(self) -> int:
        return len(self._entries)

    def lookup(self, state: VariantState | VariantBits) -> Value:
        key = _key(state)
        try:
            return self._entries[key]
        except KeyError as exc:
            raise ValueError('position is not legally reachable from 3x3 X-first opening') from exc

    def moves(self, state: VariantState | VariantBits) -> tuple[Move, ...]:
        s = state.state() if isinstance(state, VariantBits) else state
        value = self.lookup(s)
        game = VariantReference(3)
        legal = game.legal_moves(s)
        if not legal:
            return ()
        scored = [(m, self.lookup(game.apply(s,m))) for m in legal]
        if value.outcome == Outcome.WIN:
            options = [(m, v) for m,v in scored if v.outcome == Outcome.LOSS]
            target = min(v.remoteness for _,v in options)
            return tuple(m for m,v in options if v.remoteness == target)
        if value.outcome == Outcome.LOSS:
            target = max(v.remoteness for _,v in scored)
            return tuple(m for m,v in scored if v.remoteness == target)
        return tuple(m for m,v in scored if v.outcome == Outcome.NONFORCED)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description='Verify and regenerate the exact 3x3 Quixo tablebase')
    parser.add_argument('--rebuild', action='store_true', help='exhaustively run both independent solvers and verify packaged hash')
    args = parser.parse_args(argv)
    if args.rebuild:
        data, report = generate()
        if report['compressed_sha256'] != TABLEBASE_SHA256:
            raise SystemExit('FAIL: regenerated tablebase does not match committed checksum')
        print(json.dumps(report, sort_keys=True))
    else:
        t = Tablebase.load()
        root = initial(3)
        value = t.lookup(root)
        print(json.dumps({'states': t.states, 'initial_outcome': value.outcome.value,
                          'initial_remoteness_plies': value.remoteness,
                          'opening_optimal_moves': [str(m) for m in t.moves(root)]},sort_keys=True))


if __name__ == '__main__':
    main()
