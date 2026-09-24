"""
jev_engine.py - TypeSafe AI / Jev Decision Engine.
Issues structured questions (Choice, Score, Noul) in single parallel API calls.
"""

from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from dotenv import load_dotenv

from typesafe_sdk import TypeSafeClient, Choice, Score, Noul
from typesafe_sdk import TypeSafeError

# Load environment variables
load_dotenv()

# Global client instance
api_key = os.getenv("TYPESAFE_API_KEY")
client = TypeSafeClient(api_key=api_key) if api_key else None


@dataclass
class CombatDecision:
    action: str  # "ATTACK", "FLEE", "USE_POTION", "DEFEND"
    action_confidence: float
    action_probabilities: dict[str, float]
    threat_level: float  # 0 to 10
    threat_confidence: float
    use_potion_first_prob: float  # 0.0 to 1.0
    flee_worth_it_prob: float  # 0.0 to 1.0
    raw_response: dict = field(default_factory=dict)
    is_fallback: bool = False
    latency_ms: float = 0.0


@dataclass
class ExploreDecision:
    action: str  # "TAKE_TREASURE", "USE_SHRINE", "IGNORE", "SEARCH_MORE"
    action_confidence: float
    action_probabilities: dict[str, float]
    value_score: float  # 0 to 10
    value_confidence: float
    safe_to_interact_prob: float  # 0.0 to 1.0
    raw_response: dict = field(default_factory=dict)
    is_fallback: bool = False
    latency_ms: float = 0.0


@dataclass
class ForkDecision:
    path: str  # "LEFT", "RIGHT", "BACK"
    path_confidence: float
    path_probabilities: dict[str, float]
    risk_score: float  # 0 to 10
    risk_confidence: float
    raw_response: dict = field(default_factory=dict)
    is_fallback: bool = False
    latency_ms: float = 0.0


# Rubrics for Score questions (ordered criteria)
THREAT_CRITERIA = [
    "0 - Harmless nuisance with negligible damage",
    "2 - Minor threat; easily dispatched",
    "4 - Moderate opponent; requires standard combat focus",
    "6 - Dangerous foe; capable of dealing severe injuries",
    "8 - Critical threat; high risk of mortal danger",
    "10 - Catastrophic boss; overwhelming lethality",
]

VALUE_CRITERIA = [
    "0 - Worthless junk or hazardous trap with no reward",
    "2 - Minor salvage; modest pocket coins",
    "4 - Moderate find; decent gold or utility",
    "6 - Valuable cache; precious healing or rich loot",
    "8 - Highly rewarding treasure or life-saving blessing",
    "10 - Legendary hoard or game-changing restoration",
]

RISK_CRITERIA = [
    "0 - Completely secure corridor",
    "2 - Quiet passage with faint echoes",
    "4 - Uncertain path with ominous shadows",
    "6 - Treacherous path smelling of sulfur and blood",
    "8 - Highly hazardous route with lurking beasts",
    "10 - Suicide gauntlet directly into danger",
]


def jev_combat_decision(context: str, has_potions: bool = True) -> CombatDecision:
    """Ask Jev what to do in combat — 4 questions evaluated in parallel."""
    t0 = time.perf_counter()

    action_criteria = {
        "ATTACK": "Strike the enemy directly with my equipped weapon to reduce their health",
        "DEFEND": "Brace shield and adopt a defensive guard to halve incoming damage",
        "FLEE": "Attempt a hasty tactical retreat from this dangerous fight",
    }
    if has_potions:
        action_criteria["USE_POTION"] = "Drink a restorative healing potion to recover health"

    questions = {
        "action": Choice(
            instructions="What should I do this combat turn?",
            criteria=action_criteria,
        ),
        "threat_level": Score(
            instructions="On a scale of 0-10, how dangerous is this enemy to me right now given my current health and resources?",
            criteria=THREAT_CRITERIA,
        ),
        "use_potion_first": Noul(
            instructions="Should I drink a healing potion right now before taking my primary combat action?"
        ),
        "flee_worth_it": Noul(
            instructions="Is fleeing this fight worth the risk of being struck during retreat?"
        ),
    }

    try:
        if not client:
            raise RuntimeError("TypeSafeClient is not initialized. Check TYPESAFE_API_KEY in .env.")

        resp = client.system_one(state=context, questions=questions)
        latency = (time.perf_counter() - t0) * 1000

        action_ans = resp.answers.get("action")
        threat_ans = resp.answers.get("threat_level")
        potion_ans = resp.answers.get("use_potion_first")
        flee_ans = resp.answers.get("flee_worth_it")

        # Map threat score to roughly 0-10 scale based on criteria index (0-5 -> 0-10)
        raw_threat = getattr(threat_ans, "score", 5.0) if threat_ans else 5.0
        normalized_threat = min(10.0, max(0.0, round(raw_threat * 2.0, 1)))

        return CombatDecision(
            action=action_ans.choice if action_ans else "ATTACK",
            action_confidence=round(getattr(action_ans, "confidence", 0.8), 2),
            action_probabilities=getattr(action_ans, "probabilities", {}) or {},
            threat_level=normalized_threat,
            threat_confidence=round(getattr(threat_ans, "confidence", 0.7), 2),
            use_potion_first_prob=round(getattr(potion_ans, "noul", 0.1), 2),
            flee_worth_it_prob=round(getattr(flee_ans, "noul", 0.1), 2),
            raw_response=resp.answers,
            is_fallback=False,
            latency_ms=latency,
        )

    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        # Safe fallback in case of connection drop
        fallback_action = "USE_POTION" if (has_potions and "critically" in context) else "ATTACK"
        return CombatDecision(
            action=fallback_action,
            action_confidence=0.5,
            action_probabilities={fallback_action: 0.5},
            threat_level=5.0,
            threat_confidence=0.5,
            use_potion_first_prob=0.3,
            flee_worth_it_prob=0.2,
            raw_response={"error": str(exc)},
            is_fallback=True,
            latency_ms=latency,
        )


def jev_explore_decision(context: str, is_shrine: bool = False, is_treasure: bool = False, is_trap: bool = False) -> ExploreDecision:
    """Ask Jev what to do when exploring a non-combat chamber."""
    t0 = time.perf_counter()

    action_criteria = {
        "SEARCH_MORE": "Thoroughly inspect the chamber, walls, crevices, and corners for hidden secrets or coins",
        "IGNORE": "Cautiously bypass the room without touching anything to avoid lurking perils",
    }
    if is_treasure:
        action_criteria["TAKE_TREASURE"] = "Approach and open the treasure chest to claim the contents"
    elif is_shrine:
        action_criteria["USE_SHRINE"] = "Drink from or pray at the healing shrine to restore vitality"
    elif is_trap:
        action_criteria["DISARM_TRAP"] = "Carefully disarm the mechanism to safely claim trapped loot"

    questions = {
        "action": Choice(
            instructions="What should I do in this room?",
            criteria=action_criteria,
        ),
        "value_score": Score(
            instructions="On a scale of 0-10, how valuable or beneficial does interacting with this room appear?",
            criteria=VALUE_CRITERIA,
        ),
        "safe_to_interact": Noul(
            instructions="Is it safe for me to interact with this room rather than walking away?"
        ),
    }

    try:
        if not client:
            raise RuntimeError("TypeSafeClient is not initialized. Check TYPESAFE_API_KEY in .env.")

        resp = client.system_one(state=context, questions=questions)
        latency = (time.perf_counter() - t0) * 1000

        action_ans = resp.answers.get("action")
        value_ans = resp.answers.get("value_score")
        safe_ans = resp.answers.get("safe_to_interact")

        raw_val = getattr(value_ans, "score", 4.0) if value_ans else 4.0
        normalized_value = min(10.0, max(0.0, round(raw_val * 2.0, 1)))

        return ExploreDecision(
            action=action_ans.choice if action_ans else ("USE_SHRINE" if is_shrine else "TAKE_TREASURE" if is_treasure else "SEARCH_MORE"),
            action_confidence=round(getattr(action_ans, "confidence", 0.8), 2),
            action_probabilities=getattr(action_ans, "probabilities", {}) or {},
            value_score=normalized_value,
            value_confidence=round(getattr(value_ans, "confidence", 0.7), 2),
            safe_to_interact_prob=round(getattr(safe_ans, "noul", 0.8), 2),
            raw_response=resp.answers,
            is_fallback=False,
            latency_ms=latency,
        )

    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        default_act = "USE_SHRINE" if is_shrine else ("TAKE_TREASURE" if is_treasure else "SEARCH_MORE")
        return ExploreDecision(
            action=default_act,
            action_confidence=0.5,
            action_probabilities={default_act: 0.5},
            value_score=5.0,
            value_confidence=0.5,
            safe_to_interact_prob=0.7,
            raw_response={"error": str(exc)},
            is_fallback=True,
            latency_ms=latency,
        )


def jev_fork_decision(context: str, exits: list[str]) -> ForkDecision:
    """Ask Jev which direction to branch towards at a fork in the dungeon."""
    t0 = time.perf_counter()

    criteria = {}
    for exit_choice in exits:
        if exit_choice == "LEFT":
            criteria["LEFT"] = "Advance down the left stone corridor into the gloom"
        elif exit_choice == "RIGHT":
            criteria["RIGHT"] = "Advance down the right arched corridor following faint sounds"
        elif exit_choice == "BACK":
            criteria["BACK"] = "Retreat back to ensure no missed loot or safer perimeter"
        else:
            criteria[exit_choice] = f"Proceed towards {exit_choice}"

    questions = {
        "path": Choice(
            instructions="Which pathway should I take at this intersection?",
            criteria=criteria,
        ),
        "risk_level": Score(
            instructions="On a scale of 0-10, how risky does exploring deeper via this choice feel?",
            criteria=RISK_CRITERIA,
        ),
    }

    try:
        if not client:
            raise RuntimeError("TypeSafeClient is not initialized. Check TYPESAFE_API_KEY in .env.")

        resp = client.system_one(state=context, questions=questions)
        latency = (time.perf_counter() - t0) * 1000

        path_ans = resp.answers.get("path")
        risk_ans = resp.answers.get("risk_level")

        raw_risk = getattr(risk_ans, "score", 3.0) if risk_ans else 3.0
        normalized_risk = min(10.0, max(0.0, round(raw_risk * 2.0, 1)))

        return ForkDecision(
            path=path_ans.choice if path_ans else exits[0],
            path_confidence=round(getattr(path_ans, "confidence", 0.8), 2),
            path_probabilities=getattr(path_ans, "probabilities", {}) or {},
            risk_score=normalized_risk,
            risk_confidence=round(getattr(risk_ans, "confidence", 0.7), 2),
            raw_response=resp.answers,
            is_fallback=False,
            latency_ms=latency,
        )

    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000
        return ForkDecision(
            path=exits[0] if exits else "LEFT",
            path_confidence=0.5,
            path_probabilities={exits[0]: 0.5} if exits else {},
            risk_score=4.0,
            risk_confidence=0.5,
            raw_response={"error": str(exc)},
            is_fallback=True,
            latency_ms=latency,
        )
