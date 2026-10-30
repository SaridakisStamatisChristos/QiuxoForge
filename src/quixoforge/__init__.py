"""Research-grade two-player and four-player Quixo core, proofs and opponent."""
from .model import Move, State, initial, replay
from .reference import apply, legal_moves, winner
from .solver import Result, ReferenceSolver, BitboardSolver
from .reachability import ReachabilityIndex, occupancy

__all__ = ["Move", "State", "initial", "replay", "apply", "legal_moves", "winner", "Result", "ReferenceSolver", "BitboardSolver", "ReachabilityIndex", "occupancy"]

from .engine import AlphaBetaEngine, Decision
from . import teams, team_bitboard
from .generator import certify, generate
__all__ += ["AlphaBetaEngine", "Decision", "teams", "team_bitboard", "certify", "generate"]
