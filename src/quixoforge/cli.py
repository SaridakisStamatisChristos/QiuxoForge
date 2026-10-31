"""Minimal headless CLI; no UI or services required."""
import argparse
import json
from pathlib import Path
from .model import initial, replay, Move, State, X, O
from .reference import winner, legal_moves
from .puzzles import Puzzle, audit
from .solver import ReferenceSolver, BitboardSolver
from .bench import main as bench_main
from .reachability import ReachabilityIndex, occupancy
from .engine import AlphaBetaEngine
from . import teams, team_bitboard
from .generator import certify, generate
from .team_puzzles import certify as team_certify, parse_action
from .solver import ReferenceSolver, Result
from .tablebase import Tablebase
from .variants import VariantState


def main(argv=None):
    ap = argparse.ArgumentParser(prog="quixoforge")
    sub = ap.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="show a replayed position")
    show.add_argument("history", nargs="*", help="index:edge (e.g. 0:R)")
    solve = sub.add_parser("solve", help="search a bounded tactical position")
    solve.add_argument("--depth", type=int, default=2)
    solve.add_argument("history", nargs="*")
    puzzle = sub.add_parser("puzzle", help="independently audit a bounded forced win")
    puzzle.add_argument("--depth", type=int, default=1)
    puzzle.add_argument("--unique", action="store_true")
    puzzle.add_argument("history", nargs="*")
    reach = sub.add_parser("reach", help="exact reachability for boards with <=4 marks")
    reach.add_argument("--board", required=True,
                       help="25 row-major characters: '.' blank, 'X' or 'O'")
    reach.add_argument("--turn", choices=("X", "O"), default="X")
    reach.add_argument("--start", choices=("X", "O"), default="X")
    reach.add_argument("--max-stones", type=int, default=2)
    opponent = sub.add_parser("opponent", help="deterministic iterative-deepening alpha-beta recommendation (heuristic)")
    opponent.add_argument("--depth", type=int, default=3)
    opponent.add_argument("--max-nodes", type=int, default=100000)
    opponent.add_argument("history", nargs="*")
    team = sub.add_parser("team", help="official four-player play/replay and independent bounded team solver")
    team.add_argument("--depth", type=int, default=0)
    team.add_argument("history", nargs="*", help="index:edge:point or PASS")
    tc = sub.add_parser("team-certify", help="fully certify a 4-player team tactical puzzle")
    tc.add_argument("--depth",type=int,default=1)
    tc.add_argument("--unique",action="store_true")
    tc.add_argument("history",nargs="*",help="index:edge:point or PASS")
    cert = sub.add_parser("certify", help="emit fully checked tactical certificate as JSON")
    cert.add_argument("--depth", type=int, default=1)
    cert.add_argument("--unique", action="store_true")
    cert.add_argument("history", nargs="*")
    gen = sub.add_parser("generate", help="seeded, exhaustive-proof-gated tactical puzzle generator")
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--depth", type=int, default=1)
    gen.add_argument("--attempts", type=int, default=500)
    gen.add_argument("--min-plies", type=int, default=8)
    gen.add_argument("--max-plies", type=int, default=32)
    gen.add_argument("--allow-multiple", action="store_true")
    bank = sub.add_parser("generate-bank", help="create a fully certified D4-deduplicated 5x5 puzzle bank")
    bank.add_argument("--count", type=int, required=True)
    bank.add_argument("--seed", type=int, required=True)
    bank.add_argument("--depth", type=int, choices=range(1, 10), default=1)
    bank.add_argument("--searches", type=int, default=100)
    bank.add_argument("--attempts-per-search", type=int, default=100)
    bank.add_argument("--min-plies", type=int, default=8)
    bank.add_argument("--max-plies", type=int, default=32)
    bank.add_argument("--allow-multiple", action="store_true")
    bank.add_argument("--allow-shorter", action="store_true")
    bank.add_argument("--output", required=True, type=Path)
    check_bank = sub.add_parser("verify-bank", help="independently replay and verify all exported 5x5 puzzles")
    check_bank.add_argument("--input", required=True, type=Path)
    sub.add_parser("count-5x5", help="exact infinite game histories vs bounded finite puzzle-position counts")
    micro = sub.add_parser("micro", help="exact solved 3x3 Quixo tablebase; NOT the 5x5 game")
    micro.add_argument("--board", default=".........", help="nine row-major cells from .XO")
    micro.add_argument("--turn", choices=("X", "O"), default="X")
    census5 = sub.add_parser("census5", help="exact 5x5 real-board one-ply puzzle census through 5 marked cubes")
    census5.add_argument("--max-stones", type=int, default=5)
    census5.add_argument("--family", choices=("win_in_one", "unique_win_in_one"))
    census5.add_argument("--verify", action="store_true")
    depth3 = sub.add_parser("census5-depth3", help="exact 5x5 forced win by 3 for reachable K<=5 roots")
    depth3.add_argument("--verify", action="store_true")
    census = sub.add_parser("census", help="exact D4 puzzle census; 3x3 full or 5x5 sparse")
    census.add_argument("--size", type=int, choices=(3, 5), default=3)
    census.add_argument("--max-stones", type=int, default=3)
    census.add_argument("--family", choices=("P1_forced_win", "P2_unique_win",
                        "P4_unique_nontrivial_reply", "adaptive_response_win", "unique_fastest_win", "unique_max_delay"))
    census.add_argument("--verify", action="store_true")
    sub.add_parser("bench", help="use python -m quixoforge.bench for configured runs")
    args = ap.parse_args(argv)
    if args.command == "count-5x5":
        from .game_counts import count_json
        print(count_json())
        return
    if args.command == "generate-bank":
        from .catalog import generate_bank, bank_json
        dataset = generate_bank(count=args.count, seed=args.seed, depth=args.depth,
                                unique=not args.allow_multiple,
                                exact_horizon=not args.allow_shorter,
                                searches=args.searches,
                                attempts_per_search=args.attempts_per_search,
                                min_plies=args.min_plies, max_plies=args.max_plies)
        text = bank_json(dataset) + "\n"
        tmp = args.output.with_name(args.output.name + ".tmp")
        tmp.write_text(text, encoding="utf8")
        tmp.replace(args.output)
        print(json.dumps({"output": str(args.output), "count": dataset["generated"],
                          "depth": dataset["depth"], "unique": dataset["unique"],
                          "exact_horizon": dataset["exact_horizon"]}, sort_keys=True))
        return
    if args.command == "verify-bank":
        from .catalog import verify_bank
        dataset = json.loads(args.input.read_text(encoding="utf8"))
        verified = verify_bank(dataset)
        print(json.dumps({"verified": verified, "status": "PASS",
                          "input": str(args.input)}, sort_keys=True))
        return
    if args.command == "census5-depth3":
        from .census5_forced3 import main as depth3_main
        depth3_main(["--verify"] if args.verify else [])
        return
    if args.command == "census5":
        from .census5_tactical import main as census5_main
        argv = ["--max-stones", str(args.max_stones)]
        if args.family:
            argv += ["--family", args.family]
        if args.verify:
            argv += ["--verify"]
        census5_main(argv)
        return
    if args.command == "census":
        from .census import main as census_main
        argv = ["--size", str(args.size), "--max-stones", str(args.max_stones)]
        if args.family:
            argv += ["--family", args.family]
        if args.verify:
            argv += ["--verify"]
        census_main(argv)
        return
    if args.command == "bench":
        bench_main([])
        return
    if args.command == "micro":
        if len(args.board) != 9 or any(c not in ".XO" for c in args.board):
            ap.error("--board must be exactly nine characters from .XO")
        state = VariantState(tuple({".": 0, "X": X, "O": O}[v] for v in args.board),
                             {"X": X, "O": O}[args.turn], 3)
        tablebase = Tablebase.load()
        try:
            value = tablebase.lookup(state)
        except ValueError as exc:
            ap.error(str(exc))
        print(json.dumps({"variant": "3x3", "outcome": value.outcome.value,
                          "remoteness_plies": value.remoteness,
                          "optimal_moves": [str(m) for m in tablebase.moves(state)],
                          "tablebase_states": tablebase.states}, sort_keys=True))
        return
    if args.command == "reach":
        if len(args.board) != 25 or any(c not in ".XO" for c in args.board):
            ap.error("--board must contain exactly 25 characters from .XO")
        if not 0 <= args.max_stones <= 4:
            ap.error("--max-stones must be in 0..4")
        current = State(tuple({".": 0, "X": X, "O": O}[c] for c in args.board),
                        {"X": X, "O": O}[args.turn])
        if occupancy(current) > args.max_stones:
            print(json.dumps({"status": "OUT_OF_SCOPE", "max_stones": args.max_stones}))
            return
        index = ReachabilityIndex.build(args.max_stones, start={"X": X, "O": O}[args.start])
        witness = index.witness(current)
        print(json.dumps({"status": "REACHABLE" if witness is not None else "UNREACHABLE",
                          "witness": [str(m) for m in witness] if witness is not None else None,
                          "index_states": index.state_count,
                          "examined_edges": index.examined_edges}))
        return
    if args.command == "team-certify":
        try:
            actions = tuple(parse_action(a) for a in args.history)
        except ValueError as exc:
            ap.error(str(exc))
        print(json.dumps(team_certify(actions, args.depth, unique=args.unique),sort_keys=True))
        return
    if args.command == "generate":
        print(json.dumps(generate(seed=args.seed, bound=args.depth, attempts=args.attempts,
                                  min_plies=args.min_plies, max_plies=args.max_plies,
                                  unique=not args.allow_multiple), sort_keys=True))
        return
    if args.command == "team":
        try:
            history = tuple(parse_action(token) for token in args.history)
        except ValueError as exc:
            ap.error(str(exc))
        state = teams.replay(history)
        bits = team_bitboard.TeamBits.from_state(state)
        if args.depth < 0:
            ap.error("--depth must not be negative")
        a = ReferenceSolver(teams.FourPlayerGame()).solve(state,args.depth)
        b = ReferenceSolver(team_bitboard.BitboardFourPlayerGame()).solve(bits,args.depth)
        if a != b:
            raise AssertionError("four-player independent solver disagreement")
        print(json.dumps({"cells": list(state.cells), "seat": state.seat, "ply": state.ply,
                          "winner": teams.winner(state),
                          "legal": [str(m) for m in teams.legal_moves(state)],
                          "bounded_result": a.value, "depth": args.depth}, sort_keys=True))
        return
    hist = tuple(Move.parse(s) for s in args.history)
    s = replay(hist)
    if args.command == "opponent":
        outcome = AlphaBetaEngine().recommend(s, depth=args.depth, max_nodes=args.max_nodes)
        print(json.dumps({"move": str(outcome.move) if outcome.move else None,
                          "score": outcome.score, "completed_depth": outcome.completed_depth,
                          "nodes": outcome.nodes, "pv": [str(m) for m in outcome.pv],
                          "aborted": outcome.aborted,
                          "claim": "heuristic minimax; not an exact game-theoretic outcome"}, sort_keys=True))
    elif args.command == "certify":
        print(json.dumps(certify(hist, args.depth, unique=args.unique), sort_keys=True))
    elif args.command == "show":
        print(s, f"\nturn={s.turn}, winner={winner(s)}, legal={len(legal_moves(s))}")
    elif args.command == "solve":
        a = ReferenceSolver().solve(s, args.depth)
        b = BitboardSolver().solve(s, args.depth)
        if a != b:
            raise AssertionError("independent solver disagreement")
        print(json.dumps({"outcome": a.value, "depth": args.depth}))
    else:
        ans = audit(Puzzle(hist, args.depth), require_unique=args.unique)
        print(json.dumps({"minimal_bound": ans.minimal_bound,
                          "difficulty": ans.difficulty,
                          "solutions": [str(m) for m in ans.solutions]}))

if __name__ == "__main__":
    main()
