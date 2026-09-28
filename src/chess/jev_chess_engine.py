"""
jev_chess_engine.py - TypeSafe AI / Jev System One Chess Decision Engine.
Issues structured questions (Choice, Score, Noul) in single parallel API calls
to decide moves for White and Black autonomous agents.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import os
import random
import time
from typing import Any, Optional
from dotenv import load_dotenv

from typesafe_sdk import TypeSafeClient, Choice, Score, Noul

from .state_builder import (
    build_chess_context,
    build_candidate_moves_criteria,
)

# Load environment variables
load_dotenv()

api_key = os.getenv("TYPESAFE_API_KEY")
client = TypeSafeClient(api_key=api_key) if api_key else None


@dataclass
class ChessAgentProfile:
    name: str
    color: str  # "white" or "black"
    persona: str
    description: str


DEFAULT_WHITE_PROFILE = ChessAgentProfile(
    name="Jev White (Apollo)",
    color="white",
    persona="Classical Aggressive Grandmaster who values initiative, rapid development, and central space control",
    description="Strikes proactively, challenges the center with classical opening principles, and searches for tactical breakthroughs.",
)

DEFAULT_BLACK_PROFILE = ChessAgentProfile(
    name="Jev Black (Kronos)",
    color="black",
    persona="Hypermodern Counter-Attacking Grandmaster who values dynamic imbalance, King safety, and defensive resilience",
    description="Absorbs initial pressure, coordinates pieces efficiently, and counter-strikes when the opponent overextends.",
)


@dataclass
class ChessAgentDecision:
    move: str  # SAN string, e.g. "e4", "Nf3", "O-O"
    confidence: float
    probabilities: dict[str, float]
    eval_score: float  # 0.0 (losing) to 10.0 (winning)
    tactical_sharpness: float  # 0.0 to 1.0
    reasoning: str
    is_fallback: bool
    latency_ms: float
    agent_name: str
    color: str
    raw_response: dict[str, Any] = field(default_factory=dict)


# Evaluative rubric for Score question (0 to 10)
EVAL_CRITERIA = [
    "0 - Catastrophic deficit; facing forced checkmate or lost major material",
    "2 - Decisive disadvantage; heavily dominated by opponent pieces",
    "4 - Slight disadvantage; opponent holds tempo and pawn structure advantage",
    "5 - Equal equilibrium; balanced chances and mutual piece activity",
    "6 - Slight advantage; active piece placement or central pressure",
    "8 - Clear winning advantage; decisive material gain or unstoppable attack",
    "10 - Forced checkmate or completely overwhelming position",
]


def heuristic_fallback_move(legal_moves: list[dict[str, Any] | str], color: str) -> str:
    """
    Selects a high-quality legal move deterministically when API calls are unavailable.
    Prioritizes captures (Q > R > B/N > P), checks, castling, and central development.
    """
    if not legal_moves:
        return "e4" if color == "white" else "e5"

    scored: list[tuple[int, str]] = []

    for item in legal_moves:
        if isinstance(item, str):
            san = item
            score = 10
            if "x" in san:
                score += 50
                if "Q" in san:
                    score += 40
                elif "R" in san:
                    score += 25
                elif any(p in san for p in ("B", "N")):
                    score += 15
            if "+" in san or "#" in san:
                score += 35
            if san in ("O-O", "O-O-O"):
                score += 30
            if any(sq in san for sq in ("e4", "d4", "e5", "d5")):
                score += 20
            if any(sq in san for sq in ("Nf3", "Nc3", "Nf6", "Nc6", "Bc4", "Bb5", "Be7")):
                score += 15
            scored.append((score, san))
        else:
            san = item.get("san", "")
            score = 10
            if item.get("captured"):
                score += 50
            if "+" in san or "#" in san:
                score += 35
            if item.get("flags") in ("k", "q"):
                score += 30
            to_sq = item.get("to", "")
            if to_sq in ("e4", "d4", "e5", "d5"):
                score += 20
            scored.append((score, san))

    # Sort descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def jev_chess_decision(
    fen: str,
    color: str,
    legal_moves: list[dict[str, Any] | str],
    profile: Optional[ChessAgentProfile] = None,
    history: Optional[list[str]] = None,
    in_check: bool = False,
) -> ChessAgentDecision:
    """
    Queries JEV System One with structured Choice, Score, and Noul questions
    to evaluate the board and select the best move for White or Black.
    """
    t0 = time.perf_counter()

    if profile is None:
        profile = DEFAULT_WHITE_PROFILE if color == "white" else DEFAULT_BLACK_PROFILE

    # Extract clean list of SAN strings
    san_list: list[str] = [
        m if isinstance(m, str) else m.get("san", "")
        for m in legal_moves
    ]
    san_list = [s for s in san_list if s]

    if not san_list:
        fallback_move = "e4" if color == "white" else "e5"
        return ChessAgentDecision(
            move=fallback_move,
            confidence=0.5,
            probabilities={fallback_move: 1.0},
            eval_score=5.0,
            tactical_sharpness=0.1,
            reasoning="No legal moves provided; using default opening square.",
            is_fallback=True,
            latency_ms=0.0,
            agent_name=profile.name,
            color=color,
        )

    # Build prompt context and choice criteria
    context = build_chess_context(
        fen=fen,
        color=color,
        agent_name=profile.name,
        agent_persona=profile.persona,
        recent_history=history,
        in_check=in_check,
    )
    criteria = build_candidate_moves_criteria(legal_moves, color=color, max_candidates=35)

    # If criteria dictionary is empty for any reason, populate directly from san_list
    if not criteria:
        criteria = {san: f"Advance move {san}" for san in san_list[:30]}

    questions = {
        "move": Choice(
            instructions=f"Select the single best chess move for {color.capitalize()} in this position from the candidate moves.",
            criteria=criteria,
        ),
        "eval_score": Score(
            instructions=f"On a scale of 0 to 10, evaluate {color.capitalize()}'s position and winning chances.",
            criteria=EVAL_CRITERIA,
        ),
        "tactical_sharpness": Noul(
            instructions="Is this position tactically sharp with imminent tactical attacks, threats, or sacrifices?"
        ),
    }

    try:
        if not client:
            raise RuntimeError("TypeSafeClient is not initialized. Check TYPESAFE_API_KEY in .env.")

        resp = client.system_one(state=context, questions=questions)
        latency = (time.perf_counter() - t0) * 1000

        move_ans = resp.answers.get("move")
        eval_ans = resp.answers.get("eval_score")
        sharpness_ans = resp.answers.get("tactical_sharpness")

        chosen_move = getattr(move_ans, "choice", None)
        confidence = round(float(getattr(move_ans, "confidence", 0.8)), 2)
        probabilities = getattr(move_ans, "probabilities", {}) or {}

        # Validate that the chosen move is strictly in the legal moves list
        if not chosen_move or chosen_move not in san_list:
            # If the model chose a move not strictly legal, pick highest prob legal move or fallback
            valid_candidates = [m for m in probabilities if m in san_list]
            if valid_candidates:
                chosen_move = max(valid_candidates, key=lambda m: probabilities.get(m, 0.0))
            else:
                chosen_move = heuristic_fallback_move(legal_moves, color)
                confidence = 0.5

        raw_eval = getattr(eval_ans, "score", 3.0) if eval_ans else 3.0
        normalized_eval = min(10.0, max(0.0, round(float(raw_eval) * 1.67, 1)))

        sharpness_val = round(float(getattr(sharpness_ans, "noul", 0.3)), 2)

        desc = criteria.get(chosen_move, f"Execute tactical move {chosen_move}")

        return ChessAgentDecision(
            move=chosen_move,
            confidence=confidence,
            probabilities=probabilities,
            eval_score=normalized_eval,
            tactical_sharpness=sharpness_val,
            reasoning=desc,
            is_fallback=False,
            latency_ms=round(latency, 1),
            agent_name=profile.name,
            color=color,
            raw_response=getattr(resp, "answers", {}),
        )

    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        chosen_fallback = heuristic_fallback_move(legal_moves, color)
        desc = criteria.get(chosen_fallback, f"Play solid legal move {chosen_fallback}")

        return ChessAgentDecision(
            move=chosen_fallback,
            confidence=0.6,
            probabilities={chosen_fallback: 0.6},
            eval_score=5.0,
            tactical_sharpness=0.25,
            reasoning=f"{desc} (Tactical fallback: {str(exc)[:60]})",
            is_fallback=True,
            latency_ms=round(latency, 1),
            agent_name=profile.name,
            color=color,
            raw_response={"error": str(exc)},
        )
