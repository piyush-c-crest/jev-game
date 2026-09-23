"""
state_builder.py - Converts dungeon and player state into rich natural language context for Jev.
"""

from __future__ import annotations
from world import JevPlayer, Room, Enemy, RoomType


def build_combat_context(player: JevPlayer, enemy: Enemy, room: Room) -> str:
    """Build natural language state context for a combat encounter."""
    health_ratio = player.health / player.max_health
    condition_desc = (
        "critically wounded and in mortal peril" if health_ratio < 0.3 else
        "injured and battered" if health_ratio < 0.6 else
        "in good fighting condition"
    )

    potion_advice = (
        f"I have {player.potions} healing potion(s) in my bag." if player.potions > 0
        else "I am out of healing potions!"
    )

    return (
        f"I am Jev, an autonomous adventurer fighting on Floor {player.floor} of the dungeon. "
        f"Location: {room.name} ({room.description}). "
        f"My Current State: Health is {player.health}/{player.max_health} ({condition_desc}). "
        f"Stats: Attack Power = {player.attack}, Defense = {player.defense}. "
        f"Resources: {potion_advice} Gold = {player.gold}. "
        f"Track Record: Cleared {player.rooms_cleared} rooms and defeated {player.kills} monsters so far. "
        f"Opponent: {enemy.name}. Description: {enemy.description}. "
        f"Enemy Stats: Approximately {enemy.health}/{enemy.max_health} HP remaining, deals ~{enemy.attack} base damage, defense {enemy.defense}."
    )


def build_explore_context(player: JevPlayer, room: Room) -> str:
    """Build natural language state context for exploration (Treasure, Shrine, Trap, Empty)."""
    room_details = []
    if room.room_type == RoomType.TREASURE:
        room_details.append(f"There is a gleaming treasure chest containing {room.gold} gold.")
        if room.has_potion:
            room_details.append("A glowing crimson healing potion bottle sits beside the chest.")
    elif room.room_type == RoomType.SHRINE:
        room_details.append(
            f"An ancient shrine emits restorative magic capable of restoring approximately {room.shrine_heal} HP."
        )
    elif room.room_type == RoomType.TRAP:
        room_details.append(
            f"A suspicious corridor reveals rigged tripwires and spike mechanisms. Triggering it could deal ~{room.trap_damage} damage."
        )
        if room.gold > 0:
            room_details.append(f"A pouch with {room.gold} gold lies caught within the trap mechanism.")
    else:  # EMPTY
        room_details.append("The room is silent. Shadows flicker across the cold stone walls.")
        if room.gold > 0:
            room_details.append(f"You spot {room.gold} coins scattered on the floor.")
        if room.has_potion:
            room_details.append("An abandoned potion flask is tucked into a wall crevice.")

    content_str = " ".join(room_details)

    return (
        f"I am Jev, exploring Floor {player.floor} of the dungeon. "
        f"Current Location: {room.name}. "
        f"Environment: {room.description}. "
        f"Room contents: {content_str} "
        f"My Health: {player.health}/{player.max_health}. "
        f"Inventory: {player.potions} potion(s), {player.gold} gold. "
        f"Rooms cleared: {player.rooms_cleared}."
    )


def build_fork_context(player: JevPlayer, room: Room) -> str:
    """Build natural language state context when facing branching paths."""
    exits_str = ", ".join(room.exits)
    return (
        f"I am Jev, navigating Floor {player.floor} of the dungeon. "
        f"I have arrived at an intersection in {room.name}. "
        f"The stone passage diverges into several directions: {exits_str}. "
        f"My current health is {player.health}/{player.max_health}. "
        f"I have {player.potions} potion(s) and {player.gold} gold. "
        f"I need to choose the best strategic route forward to advance deeper into the dungeon."
    )
