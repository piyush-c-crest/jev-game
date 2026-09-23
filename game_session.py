"""
game_session.py - Central Game Session & State Manager for Jev Plays the Game.
Supports both manual human play and autonomous Jev agent play with full serialization.
"""

from __future__ import annotations
import copy
import random
from typing import Any, Optional

from world import JevPlayer, Dungeon, Room, RoomType, Enemy
from state_builder import build_combat_context, build_explore_context, build_fork_context
from jev_engine import (
    jev_combat_decision,
    jev_explore_decision,
    jev_fork_decision,
    CombatDecision,
    ExploreDecision,
    ForkDecision,
)
from action_resolver import resolve_combat, resolve_explore, resolve_fork, TurnOutcome, strip_markup


class GameSession:
    def __init__(self, floors: int = 5, mode: str = "manual", seed: Optional[int] = None):
        self.total_floors = floors
        self.mode = mode  # "manual" or "agent"
        self.seed = seed
        if seed is not None:
            random.seed(seed)

        self.player = JevPlayer()
        self.dungeon = Dungeon(total_floors=floors)
        self.current_floor = 1
        self.current_room_index = 0
        self.status = "PLAYING"  # "PLAYING", "VICTORY", "GAME_OVER"
        self.logs: list[dict[str, Any]] = []
        self.last_decision: Optional[dict[str, Any]] = None
        self.last_outcome: Optional[dict[str, Any]] = None
        self.last_advice: Optional[dict[str, Any]] = None

        self._init_session()

    def _init_session(self):
        self.add_log(
            "⚔️ The adventure begins. Jev steps into the foreboding dungeon entrance.",
            log_type="info",
        )
        self.add_log(
            f"🎒 Equipped: Health {self.player.health}/{self.player.max_health}, 2 Potions, Atk {self.player.attack}, Def {self.player.defense}.",
            log_type="info",
        )
        self._on_enter_room()

    def add_log(self, text: str, log_type: str = "info"):
        self.logs.append({
            "turn": self.player.total_turns,
            "text": strip_markup(text),
            "type": log_type,
        })
        # Keep recent 120 logs
        if len(self.logs) > 120:
            self.logs.pop(0)

    @property
    def current_room(self) -> Optional[Room]:
        return self.dungeon.get_room(self.current_floor, self.current_room_index)

    def _on_enter_room(self):
        room = self.current_room
        if not room:
            return

        self.player.floor = self.current_floor
        self.player.current_room_index = self.current_room_index

        self.add_log(
            f"🚪 Entered Floor {self.current_floor}, Room {self.current_room_index + 1}: {room.name}",
            log_type="info",
        )

        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            self.add_log(
                f"⚠️ Hostile Encounter! {room.enemy.name} emerges: {room.enemy.description}",
                log_type="danger",
            )
        elif room.room_type == RoomType.TREASURE:
            self.add_log(
                f"💎 Gilded Vault! An ornate chest rests on a stone pedestal with {room.gold} gold.",
                log_type="loot",
            )
        elif room.room_type == RoomType.SHRINE:
            self.add_log(
                "✨ Celestial Shrine! A soothing celestial fountain radiates healing light.",
                log_type="loot",
            )
        elif room.room_type == RoomType.TRAP:
            self.add_log(
                "⚠️ Perilous Passage! Floor pressure plates and tripwires detect your arrival.",
                log_type="danger",
            )
        elif room.room_type == RoomType.FORK:
            self.add_log(
                f"🧭 Crossroads! The stone corridor branches into paths: {', '.join(room.exits)}.",
                log_type="info",
            )

    def get_available_actions(self) -> list[str]:
        if self.status != "PLAYING":
            return []

        room = self.current_room
        if not room:
            return []

        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            return ["ATTACK", "DEFEND", "USE_POTION", "FLEE"]
        elif room.room_type == RoomType.TREASURE:
            return ["TAKE_TREASURE", "SEARCH_MORE", "IGNORE"]
        elif room.room_type == RoomType.SHRINE:
            return ["USE_SHRINE", "SEARCH_MORE", "IGNORE"]
        elif room.room_type == RoomType.TRAP:
            return ["DISARM_TRAP", "SEARCH_MORE", "IGNORE"]
        elif room.room_type == RoomType.FORK:
            return room.exits or ["LEFT", "RIGHT", "BACK"]
        else:  # EMPTY
            return ["SEARCH_MORE", "IGNORE"]

    def get_encounter_phase(self) -> str:
        if self.status != "PLAYING":
            return "finished"
        room = self.current_room
        if not room:
            return "none"
        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            return "combat"
        elif room.room_type == RoomType.FORK:
            return "fork"
        elif not room.cleared:
            return "explore"
        return "cleared"

    def execute_player_action(self, action: str) -> dict[str, Any]:
        """Execute a human player turn with the requested action."""
        if self.status != "PLAYING":
            return self.get_state()

        action = action.upper().strip()
        room = self.current_room
        if not room:
            return self.get_state()

        self.player.total_turns += 1
        outcome: TurnOutcome

        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            outcome = resolve_combat(self.player, room.enemy, action)
            self._handle_combat_outcome(outcome, room)
        elif room.room_type == RoomType.FORK:
            outcome = resolve_fork(self.player, room, action)
            self._handle_non_combat_outcome(outcome, room)
        else:
            outcome = resolve_explore(self.player, room, action)
            self._handle_non_combat_outcome(outcome, room)

        self.last_outcome = outcome.to_dict()
        self.last_decision = None
        self.last_advice = None
        return self.get_state()

    def execute_agent_turn(self) -> dict[str, Any]:
        """Execute an autonomous agent turn using Jev System One."""
        if self.status != "PLAYING":
            return self.get_state()

        room = self.current_room
        if not room:
            return self.get_state()

        self.player.total_turns += 1
        outcome: TurnOutcome

        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            context = build_combat_context(self.player, room.enemy, room)
            decision = jev_combat_decision(context, has_potions=(self.player.potions > 0))
            self.last_decision = {
                "type": "combat",
                "action": decision.action,
                "confidence": decision.action_confidence,
                "probabilities": decision.action_probabilities,
                "threat_level": decision.threat_level,
                "threat_confidence": decision.threat_confidence,
                "use_potion_first_prob": decision.use_potion_first_prob,
                "flee_worth_it_prob": decision.flee_worth_it_prob,
                "latency_ms": round(decision.latency_ms, 1),
                "is_fallback": decision.is_fallback,
            }
            outcome = resolve_combat(self.player, room.enemy, decision)
            self._handle_combat_outcome(outcome, room)

        elif room.room_type == RoomType.FORK:
            context = build_fork_context(self.player, room)
            f_decision = jev_fork_decision(context, room.exits or ["LEFT", "RIGHT", "BACK"])
            self.last_decision = {
                "type": "fork",
                "action": f_decision.path,
                "confidence": f_decision.path_confidence,
                "probabilities": f_decision.path_probabilities,
                "risk_score": f_decision.risk_score,
                "risk_confidence": f_decision.risk_confidence,
                "latency_ms": round(f_decision.latency_ms, 1),
                "is_fallback": f_decision.is_fallback,
            }
            outcome = resolve_fork(self.player, room, f_decision)
            self._handle_non_combat_outcome(outcome, room)

        else:
            context = build_explore_context(self.player, room)
            e_decision = jev_explore_decision(
                context,
                is_shrine=(room.room_type == RoomType.SHRINE),
                is_treasure=(room.room_type == RoomType.TREASURE),
                is_trap=(room.room_type == RoomType.TRAP),
            )
            self.last_decision = {
                "type": "explore",
                "action": e_decision.action,
                "confidence": e_decision.action_confidence,
                "probabilities": e_decision.action_probabilities,
                "value_score": e_decision.value_score,
                "value_confidence": e_decision.value_confidence,
                "safe_to_interact_prob": e_decision.safe_to_interact_prob,
                "latency_ms": round(e_decision.latency_ms, 1),
                "is_fallback": e_decision.is_fallback,
            }
            outcome = resolve_explore(self.player, room, e_decision)
            self._handle_non_combat_outcome(outcome, room)

        self.last_outcome = outcome.to_dict()
        self.last_advice = None
        return self.get_state()

    def get_agent_advice(self) -> dict[str, Any]:
        """Consult Jev System One without committing or advancing the turn."""
        if self.status != "PLAYING":
            return {"error": "Game is not active"}

        room = self.current_room
        if not room:
            return {"error": "No active room"}

        if room.room_type in (RoomType.ENEMY, RoomType.BOSS) and room.enemy and room.enemy.is_alive():
            context = build_combat_context(self.player, room.enemy, room)
            d = jev_combat_decision(context, has_potions=(self.player.potions > 0))
            advice = {
                "type": "combat",
                "action": d.action,
                "confidence": d.action_confidence,
                "probabilities": d.action_probabilities,
                "threat_level": d.threat_level,
                "threat_confidence": d.threat_confidence,
                "use_potion_first_prob": d.use_potion_first_prob,
                "flee_worth_it_prob": d.flee_worth_it_prob,
                "latency_ms": round(d.latency_ms, 1),
                "is_fallback": d.is_fallback,
            }
        elif room.room_type == RoomType.FORK:
            context = build_fork_context(self.player, room)
            d = jev_fork_decision(context, room.exits or ["LEFT", "RIGHT", "BACK"])
            advice = {
                "type": "fork",
                "action": d.path,
                "confidence": d.path_confidence,
                "probabilities": d.path_probabilities,
                "risk_score": d.risk_score,
                "risk_confidence": d.risk_confidence,
                "latency_ms": round(d.latency_ms, 1),
                "is_fallback": d.is_fallback,
            }
        else:
            context = build_explore_context(self.player, room)
            d = jev_explore_decision(
                context,
                is_shrine=(room.room_type == RoomType.SHRINE),
                is_treasure=(room.room_type == RoomType.TREASURE),
                is_trap=(room.room_type == RoomType.TRAP),
            )
            advice = {
                "type": "explore",
                "action": d.action,
                "confidence": d.action_confidence,
                "probabilities": d.action_probabilities,
                "value_score": d.value_score,
                "value_confidence": d.value_confidence,
                "safe_to_interact_prob": d.safe_to_interact_prob,
                "latency_ms": round(d.latency_ms, 1),
                "is_fallback": d.is_fallback,
            }

        self.last_advice = advice
        return advice

    def _handle_combat_outcome(self, outcome: TurnOutcome, room: Room):
        for detail in outcome.clean_details or outcome.details:
            log_type = "combat"
            if "vanquished" in detail or "gold" in detail:
                log_type = "loot"
            elif "CRITICAL" in detail or "slashing" in detail or "struck" in detail:
                log_type = "danger"
            self.add_log(detail, log_type=log_type)

        if outcome.player_died:
            self.status = "GAME_OVER"
            self.add_log(f"💀 Defeated by {room.enemy.name if room.enemy else 'foe'} on Floor {self.current_floor}!", log_type="danger")
            return

        if outcome.enemy_defeated:
            room.cleared = True
            if room.room_type == RoomType.BOSS and self.current_floor == self.total_floors:
                self.status = "VICTORY"
                self.add_log("👑 VICTORY! The Ancient Dragon is slain! The dungeon is conquered!", log_type="loot")
                return
            self._advance_room()

        elif outcome.escaped:
            room.cleared = True
            self.add_log("🏃 Safely escaped the hostile chamber.", log_type="info")
            self._advance_room()

    def _handle_non_combat_outcome(self, outcome: TurnOutcome, room: Room):
        for detail in outcome.clean_details or outcome.details:
            log_type = "loot" if ("gold" in detail or "restoring" in detail or "Potion" in detail) else "info"
            if "Trap Triggered" in detail or "damage" in detail:
                log_type = "danger"
            self.add_log(detail, log_type=log_type)

        if outcome.player_died:
            self.status = "GAME_OVER"
            self.add_log(f"💀 Perished in {room.name} on Floor {self.current_floor}!", log_type="danger")
            return

        self._advance_room()

    def _advance_room(self):
        self.player.rooms_cleared += 1
        rooms_count = self.dungeon.total_rooms_on_floor(self.current_floor)

        if self.current_room_index + 1 < rooms_count:
            self.current_room_index += 1
            self._on_enter_room()
        else:
            # Floor completed!
            if self.current_floor < self.total_floors:
                self._handle_floor_checkpoint()
            else:
                self.status = "VICTORY"
                self.add_log("👑 VICTORY! All dungeon floors cleared!", log_type="loot")

    def _handle_floor_checkpoint(self):
        heal_val = min(20, self.player.max_health - self.player.health)
        self.player.health += heal_val

        self.add_log(
            f"🌟 Floor {self.current_floor} Cleared! Reached the downward stairway.",
            log_type="loot",
        )

        bought_msg = ""
        if self.player.gold >= 30 and self.player.potions < 2:
            self.player.gold -= 30
            self.player.potions += 1
            bought_msg = " Bought 1 Potion for 30 Gold."

        self.add_log(
            f"⛺ Camp Rest: Restored +{heal_val} HP (Health: {self.player.health}/{self.player.max_health}).{bought_msg}",
            log_type="info",
        )

        self.current_floor += 1
        self.current_room_index = 0
        self._on_enter_room()

    def get_state(self) -> dict[str, Any]:
        """Serialize complete game state into a clean dictionary."""
        room = self.current_room
        rooms_count = self.dungeon.total_rooms_on_floor(self.current_floor)

        # Floor progress nodes
        floor_progress = []
        for i in range(rooms_count):
            r = self.dungeon.get_room(self.current_floor, i)
            if i < self.current_room_index:
                p_status = "cleared"
            elif i == self.current_room_index:
                p_status = "current"
            else:
                p_status = "upcoming"

            rtype = r.room_type.value if r else "unknown"
            floor_progress.append({
                "index": i,
                "status": p_status,
                "type": rtype,
                "is_boss": (r.room_type == RoomType.BOSS) if r else False,
            })

        room_dict = None
        if room:
            enemy_dict = None
            if room.enemy:
                enemy_dict = {
                    "name": room.enemy.name,
                    "health": room.enemy.health,
                    "max_health": room.enemy.max_health,
                    "attack": room.enemy.attack,
                    "defense": room.enemy.defense,
                    "reward_gold": room.enemy.reward_gold,
                    "description": room.enemy.description,
                    "is_alive": room.enemy.is_alive(),
                }

            room_dict = {
                "type": room.room_type.value,
                "name": room.name,
                "description": room.description,
                "cleared": room.cleared,
                "enemy": enemy_dict,
                "gold": room.gold,
                "has_potion": room.has_potion,
                "trap_damage": room.trap_damage,
                "shrine_heal": room.shrine_heal,
                "exits": room.exits,
            }

        return {
            "status": self.status,
            "mode": self.mode,
            "player": {
                "health": self.player.health,
                "max_health": self.player.max_health,
                "attack": self.player.attack,
                "defense": self.player.defense,
                "potions": self.player.potions,
                "gold": self.player.gold,
                "floor": self.player.floor,
                "rooms_cleared": self.player.rooms_cleared,
                "total_turns": self.player.total_turns,
                "kills": self.player.kills,
                "is_alive": self.player.is_alive(),
            },
            "dungeon": {
                "total_floors": self.total_floors,
                "current_floor": self.current_floor,
                "rooms_on_floor": rooms_count,
                "current_room_index": self.current_room_index,
                "floor_progress": floor_progress,
            },
            "current_room": room_dict,
            "available_actions": self.get_available_actions(),
            "encounter_phase": self.get_encounter_phase(),
            "last_decision": self.last_decision,
            "last_outcome": self.last_outcome,
            "last_advice": self.last_advice,
            "logs": self.logs[-40:],
        }
