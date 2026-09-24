"""
game_loop.py - Core game loop and turn orchestrator for Jev Plays the Game.
Coordinates the Dungeon, State Builder, Jev Engine, Action Resolver, and UI.
"""

from __future__ import annotations
import sys
import time
from .world import JevPlayer, Dungeon, Room, RoomType
from .state_builder import build_combat_context, build_explore_context, build_fork_context
from .jev_engine import jev_combat_decision, jev_explore_decision, jev_fork_decision
from .action_resolver import resolve_combat, resolve_explore, resolve_fork
from .ui import (
    console,
    render_game_screen,
    display_intro_banner,
    display_victory_screen,
    display_game_over_screen,
)


def run_game(step_delay: float = 1.2, total_floors: int = 5) -> bool:
    """
    Run an autonomous game session of Jev Plays the Game.
    Returns True if Jev achieved victory, False otherwise.
    """
    display_intro_banner()
    time.sleep(2.0)

    player = JevPlayer()
    dungeon = Dungeon(total_floors=total_floors)
    logs: list[str] = [
        "⚔️ [bold cyan]The adventure begins.[/bold cyan] Jev steps into the foreboding dungeon entrance.",
        f"🎒 Equipped: Health 100/100, 2 Potions, Atk 15, Def 10. Heading down into Floor 1.",
    ]

    for floor_idx in range(1, total_floors + 1):
        rooms_count = dungeon.total_rooms_on_floor(floor_idx)

        for room_idx in range(rooms_count):
            if not player.is_alive():
                break

            player.floor = floor_idx
            player.current_room_index = room_idx
            room = dungeon.get_room(floor_idx, room_idx)
            if not room:
                continue

            logs.append(
                f"[bold cyan]Turn {player.total_turns + 1} |[/bold cyan] 🚪 Entered [bold white]Floor {floor_idx}, Room {room_idx + 1}: {room.name}[/bold white]"
            )

            # Initial render before decision
            render_game_screen(player, room, rooms_count, None, logs)

            # Encounter handling
            if room.room_type in (RoomType.ENEMY, RoomType.BOSS):
                enemy = room.enemy
                if enemy:
                    logs.append(
                        f"⚠️ [bold red]Hostile Encounter![/bold red] {enemy.name} emerges: [dim]{enemy.description}[/dim]"
                    )
                    render_game_screen(player, room, rooms_count, None, logs)
                    time.sleep(min(1.0, step_delay))

                    while enemy.is_alive() and player.is_alive():
                        player.total_turns += 1

                        context = build_combat_context(player, enemy, room)

                        # Query Jev with spinner
                        with console.status("[bold cyan]🧠 Jev is analyzing combat state with System One...[/bold cyan]", spinner="dots"):
                            decision = jev_combat_decision(context, has_potions=(player.potions > 0))

                        # Resolve turn
                        outcome = resolve_combat(player, enemy, decision)

                        for detail in outcome.details:
                            logs.append(f"[bold cyan]Turn {player.total_turns} |[/bold cyan] {detail}")

                        render_game_screen(player, room, rooms_count, decision, logs)

                        if outcome.player_died:
                            time.sleep(1.5)
                            display_game_over_screen(
                                player,
                                player.total_turns,
                                f"Fell in combat against {enemy.name} on Floor {floor_idx} in {room.name}."
                            )
                            return False

                        if outcome.enemy_defeated:
                            if room.room_type == RoomType.BOSS:
                                time.sleep(1.5)
                                display_victory_screen(player, player.total_turns)
                                return True
                            time.sleep(step_delay)
                            break

                        if outcome.escaped:
                            time.sleep(step_delay)
                            break

                        time.sleep(step_delay)

            elif room.room_type == RoomType.FORK:
                player.total_turns += 1
                context = build_fork_context(player, room)

                with console.status("[bold cyan]🧠 Jev is navigating crossroads with System One...[/bold cyan]", spinner="dots"):
                    decision = jev_fork_decision(context, room.exits)

                outcome = resolve_fork(player, room, decision)
                for detail in outcome.details:
                    logs.append(f"[bold cyan]Turn {player.total_turns} |[/bold cyan] {detail}")

                render_game_screen(player, room, rooms_count, decision, logs)
                time.sleep(step_delay)

            else:  # TREASURE, SHRINE, TRAP, EMPTY
                player.total_turns += 1
                context = build_explore_context(player, room)

                with console.status("[bold cyan]🧠 Jev is evaluating chamber with System One...[/bold cyan]", spinner="dots"):
                    decision = jev_explore_decision(
                        context,
                        is_shrine=(room.room_type == RoomType.SHRINE),
                        is_treasure=(room.room_type == RoomType.TREASURE),
                        is_trap=(room.room_type == RoomType.TRAP),
                    )

                outcome = resolve_explore(player, room, decision)
                for detail in outcome.details:
                    logs.append(f"[bold cyan]Turn {player.total_turns} |[/bold cyan] {detail}")

                render_game_screen(player, room, rooms_count, decision, logs)

                if outcome.player_died:
                    time.sleep(1.5)
                    display_game_over_screen(
                        player,
                        player.total_turns,
                        f"Perished from lethal trap triggers in {room.name} on Floor {floor_idx}."
                    )
                    return False

                time.sleep(step_delay)

            player.rooms_cleared += 1

        # Checkpoint between floors
        if floor_idx < total_floors and player.is_alive():
            rest_heal = min(20, player.max_health - player.health)
            player.health += rest_heal
            logs.append(
                f"🌟 [bold yellow]Floor {floor_idx} Cleared![/bold yellow] Jev reached the downward stairway."
            )
            bought_potion_msg = ""
            if player.gold >= 30 and player.potions < 2:
                player.gold -= 30
                player.potions += 1
                bought_potion_msg = " Bought 1 Potion for 30 Gold."

            logs.append(
                f"⛺ [bold green]Camp Rest:[/bold green] Restored +{rest_heal} HP (Health: {player.health}/{player.max_health}).{bought_potion_msg}"
            )
            render_game_screen(player, room, rooms_count, None, logs)
            time.sleep(step_delay * 1.5)

    if player.is_alive():
        display_victory_screen(player, player.total_turns)
        return True

    return False
