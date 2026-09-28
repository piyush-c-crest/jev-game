"""
chess_session.py - Central Match Session Manager for JEV vs JEV Chess.
Maintains the authoritative state, dual agent telemetry, history chronicle,
and turn orchestration.
"""

from __future__ import annotations
import threading
import time
from typing import Any, Optional

from .state_builder import parse_fen
from .jev_chess_engine import (
    jev_chess_decision,
    ChessAgentProfile,
    ChessAgentDecision,
    DEFAULT_WHITE_PROFILE,
    DEFAULT_BLACK_PROFILE,
)


STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class ChessSession:
    def __init__(
        self,
        starting_fen: str = STARTING_FEN,
        white_profile: Optional[ChessAgentProfile] = None,
        black_profile: Optional[ChessAgentProfile] = None,
    ):
        self.lock = threading.Lock()
        self.starting_fen = starting_fen
        self.fen = starting_fen
        self.turn = "white"  # "white" or "black"
        self.status = "PLAYING"  # "PLAYING", "CHECKMATE", "STALEMATE", "DRAW", "RESIGNED"
        self.winner: Optional[str] = None  # "white", "black", "draw"

        self.white_profile = white_profile or DEFAULT_WHITE_PROFILE
        self.black_profile = black_profile or DEFAULT_BLACK_PROFILE

        self.history: list[dict[str, Any]] = []
        self.move_count = 0
        self.last_white_decision: Optional[dict[str, Any]] = None
        self.last_black_decision: Optional[dict[str, Any]] = None
        self.last_move: Optional[dict[str, Any]] = None

        self.start_timestamp = time.time()
        self.max_moves = 200  # Prevent runaway games

    def reset(self, starting_fen: Optional[str] = None):
        """Reset the match session to the starting state."""
        with self.lock:
            self.fen = starting_fen or self.starting_fen
            self.turn = "white"
            self.status = "PLAYING"
            self.winner = None
            self.history = []
            self.move_count = 0
            self.last_white_decision = None
            self.last_black_decision = None
            self.last_move = None
            self.start_timestamp = time.time()

    def execute_agent_step(
        self,
        fen: Optional[str] = None,
        legal_moves: Optional[list[dict[str, Any] | str]] = None,
        in_check: bool = False,
        client_history: Optional[list[str]] = None,
        is_game_over: bool = False,
        game_over_reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Executes one autonomous turn by the active JEV agent (White or Black).
        Returns the updated state including the chosen move and telemetry.
        """
        with self.lock:
            if self.status != "PLAYING":
                return self.get_state()

            if is_game_over:
                self._handle_game_over(game_over_reason)
                return self.get_state()

            current_fen = fen or self.fen
            pos_info = parse_fen(current_fen)
            active_color = pos_info.active_color
            self.turn = active_color

            # Check max moves guard
            if pos_info.fullmove_number >= self.max_moves:
                self.status = "DRAW"
                self.winner = "draw"
                return self.get_state()

            # Active agent profile
            active_profile = self.white_profile if active_color == "white" else self.black_profile

            # Extract recent SAN move history strings
            recent_san_history = client_history or [m["san"] for m in self.history if "san" in m]

            # Query JEV System One for the decision
            decision: ChessAgentDecision = jev_chess_decision(
                fen=current_fen,
                color=active_color,
                legal_moves=legal_moves or [],
                profile=active_profile,
                history=recent_san_history,
                in_check=in_check,
            )

            decision_dict = {
                "move": decision.move,
                "confidence": decision.confidence,
                "probabilities": decision.probabilities,
                "eval_score": decision.eval_score,
                "tactical_sharpness": decision.tactical_sharpness,
                "reasoning": decision.reasoning,
                "is_fallback": decision.is_fallback,
                "latency_ms": decision.latency_ms,
                "agent_name": decision.agent_name,
                "color": decision.color,
                "turn_number": pos_info.fullmove_number,
            }

            if active_color == "white":
                self.last_white_decision = decision_dict
            else:
                self.last_black_decision = decision_dict

            self.move_count += 1
            move_record = {
                "ply": self.move_count,
                "turn": pos_info.fullmove_number,
                "color": active_color,
                "san": decision.move,
                "agent": active_profile.name,
                "confidence": decision.confidence,
                "eval": decision.eval_score,
                "latency_ms": decision.latency_ms,
                "is_fallback": decision.is_fallback,
            }
            self.history.append(move_record)
            self.last_move = move_record

            # Toggle turn expectation
            self.turn = "black" if active_color == "white" else "white"

            return self.get_state()

    def _handle_game_over(self, reason: Optional[str] = None):
        """Set terminal game status."""
        reason_str = (reason or "").lower()
        if "checkmate" in reason_str:
            self.status = "CHECKMATE"
            # The player who just moved won
            self.winner = "black" if self.turn == "white" else "white"
        elif "stalemate" in reason_str:
            self.status = "STALEMATE"
            self.winner = "draw"
        elif "repetition" in reason_str or "draw" in reason_str or "insufficient" in reason_str or "50-move" in reason_str:
            self.status = "DRAW"
            self.winner = "draw"
        else:
            self.status = "GAME_OVER"
            self.winner = "draw"

    def get_state(self) -> dict[str, Any]:
        """Serialize complete game session into a clean dictionary."""
        pos_info = parse_fen(self.fen)
        elapsed = round(time.time() - self.start_timestamp, 1)

        # Format PGN-like move log
        pgn_rows = []
        white_move = None
        for m in self.history:
            if m["color"] == "white":
                white_move = m["san"]
            else:
                turn_num = m["turn"]
                pgn_rows.append({
                    "turn": turn_num,
                    "white": white_move or "",
                    "black": m["san"],
                })
                white_move = None
        if white_move:
            pgn_rows.append({
                "turn": (self.history[-1]["turn"] if self.history else 1),
                "white": white_move,
                "black": "",
            })

        return {
            "status": self.status,
            "winner": self.winner,
            "turn": self.turn,
            "fen": self.fen,
            "move_count": self.move_count,
            "fullmove_number": pos_info.fullmove_number,
            "game_phase": pos_info.game_phase,
            "material": {
                "white": pos_info.white_material,
                "black": pos_info.black_material,
                "difference": pos_info.material_difference,
                "captured_by_white": pos_info.captured_by_white,
                "captured_by_black": pos_info.captured_by_black,
            },
            "white_agent": {
                "name": self.white_profile.name,
                "color": self.white_profile.color,
                "persona": self.white_profile.persona,
                "description": self.white_profile.description,
            },
            "black_agent": {
                "name": self.black_profile.name,
                "color": self.black_profile.color,
                "persona": self.black_profile.persona,
                "description": self.black_profile.description,
            },
            "last_white_decision": self.last_white_decision,
            "last_black_decision": self.last_black_decision,
            "last_move": self.last_move,
            "history": self.history[-40:],
            "pgn_moves": pgn_rows,
            "elapsed_seconds": elapsed,
        }
