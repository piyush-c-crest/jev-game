"""
RPG Module - Core game engine, session manager, actions, and terminal UI for Jev Plays the Game.
"""

from .action_resolver import TurnOutcome, resolve_combat, resolve_explore, resolve_fork
from .game_loop import run_game
from .game_session import GameSession
from .jev_engine import (
    CombatDecision,
    ExploreDecision,
    ForkDecision,
    jev_combat_decision,
    jev_explore_decision,
    jev_fork_decision,
)
from .state_builder import (
    build_combat_context,
    build_explore_context,
    build_fork_context,
)
from .world import Dungeon, Enemy, JevPlayer, Room, RoomType

__all__ = [
    "CombatDecision",
    "Dungeon",
    "Enemy",
    "ExploreDecision",
    "ForkDecision",
    "GameSession",
    "JevPlayer",
    "Room",
    "RoomType",
    "TurnOutcome",
    "build_combat_context",
    "build_explore_context",
    "build_fork_context",
    "jev_combat_decision",
    "jev_explore_decision",
    "jev_fork_decision",
    "resolve_combat",
    "resolve_explore",
    "resolve_fork",
    "run_game",
]
