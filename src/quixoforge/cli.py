"""Minimal headless CLI; no UI or services required."""
import argparse
import json
from .model import initial, replay, Move, State, X, O
from .reference import winner, legal_moves
from .puzzles import Puzzle, audit
from .solver import ReferenceSolver, BitboardSolver
from .bench import main as bench_main
from .reachability import ReachabilityIndex, occupancy


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
    reach = sub.add_parser("reach", help="exact reachability for boards with <=3 marks")
    reach.add_argument("--board", required=True,
                       help="25 row-major characters: '.' blank, 'X' or 'O'")
    reach.add_argument("--turn", choices=("X", "O"), default="X")
    reach.add_argument("--start", choices=("X", "O"), default="X")
    reach.add_argument("--max-stones", type=int, default=2)
    sub.add_parser("bench", help="use python -m quixoforge.bench for configured runs")
    args = ap.parse_args(argv)
    if args.command == "bench":
        bench_main([])
        return
    if args.command == "reach":
        if len(args.board) != 25 or any(c not in ".XO" for c in args.board):
            ap.error("--board must contain exactly 25 characters from .XO")
        if not 0 <= args.max_stones <= 3:
            ap.error("--max-stones must be in 0..3")
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
    hist = tuple(Move.parse(s) for s in args.history)
    s = replay(hist)
    if args.command == "show":
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
