"""
action_resolver.py - Maps Jev's decisions and player actions into deterministic and probabilistic game mechanics.
Supports both autonomous Jev agent decisions and direct human player choices.
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
import random
import re

from .world import JevPlayer, Room, Enemy, RoomType
from .jev_engine import CombatDecision, ExploreDecision, ForkDecision


def strip_markup(text: str) -> str:
    """Strip Rich/console style tags from text for web presentation."""
    return re.sub(r"\[/?[a-zA-Z0-9_ #]+\]", "", text)


@dataclass
class TurnOutcome:
    summary: str
    details: list[str] = field(default_factory=list)
    clean_details: list[str] = field(default_factory=list)
    damage_dealt: int = 0
    damage_taken: int = 0
    healing_done: int = 0
    gold_gained: int = 0
    potions_gained: int = 0
    potions_used: int = 0
    enemy_defeated: bool = False
    combat_ended: bool = False
    escaped: bool = False
    player_died: bool = False

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "details": self.clean_details or [strip_markup(d) for d in self.details],
            "raw_details": self.details,
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken,
            "healing_done": self.healing_done,
            "gold_gained": self.gold_gained,
            "potions_gained": self.potions_gained,
            "potions_used": self.potions_used,
            "enemy_defeated": self.enemy_defeated,
            "combat_ended": self.combat_ended,
            "escaped": self.escaped,
            "player_died": self.player_died,
        }


def resolve_combat(player: JevPlayer, enemy: Enemy, decision: CombatDecision | str) -> TurnOutcome:
    """
    Resolve a single turn of combat.
    Accepts either a CombatDecision (from Jev AI) or a string action (from human player).
    """
    details: list[str] = []
    damage_dealt = 0
    damage_taken = 0
    healing_done = 0
    potions_used = 0
    gold_gained = 0
    enemy_defeated = False
    escaped = False

    is_ai = isinstance(decision, CombatDecision)
    action = decision.action.upper() if is_ai else str(decision).upper()

    # Pre-emptive potion consumption (AI Noul trigger only)
    if is_ai and decision.use_potion_first_prob > 0.65 and player.potions > 0 and player.health < (player.max_health * 0.70) and action != "USE_POTION":
        player.potions -= 1
        potions_used += 1
        heal_val = min(40, player.max_health - player.health)
        player.health += heal_val
        healing_done += heal_val
        details.append(
            f"🧪 [bold cyan]Pre-emptive Brew:[/bold cyan] Jev quaffed a potion (+{heal_val} HP, now {player.health}/{player.max_health}) before acting!"
        )

    actor_name = "Jev" if is_ai else "You"

    if action == "ATTACK":
        # Critical strike chance 15%
        is_crit = random.random() < 0.15
        variance = random.randint(-2, 4)
        base_dmg = max(4, player.attack + variance - (enemy.defense // 2))
        dmg = int(base_dmg * 1.5) if is_crit else base_dmg

        enemy.health = max(0, enemy.health - dmg)
        damage_dealt += dmg

        if is_crit:
            details.append(
                f"💥 [bold yellow]CRITICAL STRIKE![/bold yellow] {actor_name} landed a devastating blow on {enemy.name} for [bold red]{dmg}[/bold red] damage!"
            )
        else:
            details.append(
                f"⚔️ {actor_name} struck {enemy.name} with blade for [bold red]{dmg}[/bold red] damage. ({enemy.health}/{enemy.max_health} HP remaining)"
            )

        if not enemy.is_alive():
            enemy_defeated = True
            gold_gained = enemy.reward_gold
            player.gold += gold_gained
            player.kills += 1
            details.append(
                f"💀 [bold green]{enemy.name} is vanquished![/bold green] Looted [bold yellow]+{gold_gained} gold[/bold yellow]."
            )
        else:
            # Enemy retaliates
            e_variance = random.randint(-2, 2)
            e_dmg = max(2, enemy.attack + e_variance - (player.defense // 2))
            player.health = max(0, player.health - e_dmg)
            damage_taken += e_dmg
            details.append(
                f"🩸 {enemy.name} countered aggressively, slashing for [bold magenta]{e_dmg}[/bold magenta] damage."
            )

    elif action == "DEFEND":
        # Block incoming attack and counter-jab
        e_variance = random.randint(-2, 2)
        raw_e_dmg = max(2, enemy.attack + e_variance - (player.defense // 2))
        mitigated_dmg = max(1, raw_e_dmg // 2)
        player.health = max(0, player.health - mitigated_dmg)
        damage_taken += mitigated_dmg

        # Counter-poke
        counter_dmg = max(2, (player.attack // 3) + random.randint(0, 2))
        enemy.health = max(0, enemy.health - counter_dmg)
        damage_dealt += counter_dmg

        details.append(
            f"🛡️ [bold blue]Iron Guard:[/bold blue] {actor_name} braced behind shield, reducing damage from {raw_e_dmg} to [bold magenta]{mitigated_dmg}[/bold magenta]."
        )
        details.append(
            f"🗡️ Countered with a shield bash for [bold red]{counter_dmg}[/bold red] damage."
        )

        if not enemy.is_alive():
            enemy_defeated = True
            gold_gained = enemy.reward_gold
            player.gold += gold_gained
            player.kills += 1
            details.append(
                f"💀 {enemy.name} collapsed from the shield bash! Looted [bold yellow]+{gold_gained} gold[/bold yellow]."
            )

    elif action == "USE_POTION":
        if player.potions > 0:
            player.potions -= 1
            potions_used += 1
            heal_val = min(40, player.max_health - player.health)
            player.health += heal_val
            healing_done += heal_val
            details.append(
                f"🧪 {actor_name} drank a restorative potion, recovering [bold green]+{heal_val} HP[/bold green] (Health: {player.health}/{player.max_health})."
            )
        else:
            details.append(
                f"❌ {actor_name} reached for a potion, but the bandolier was completely empty!"
            )

        # Enemy attacks during the opening
        e_variance = random.randint(-2, 2)
        e_dmg = max(2, enemy.attack + e_variance - (player.defense // 2))
        player.health = max(0, player.health - e_dmg)
        damage_taken += e_dmg
        details.append(
            f"🩸 While drinking, {enemy.name} struck for [bold magenta]{e_dmg}[/bold magenta] damage."
        )

    elif action == "FLEE":
        flee_prob = decision.flee_worth_it_prob if is_ai else 0.20
        escape_chance = 0.55 + (flee_prob * 0.25)
        if random.random() < escape_chance:
            escaped = True
            details.append(
                f"🏃💨 [bold cyan]Tactical Disengagement:[/bold cyan] {actor_name} deftly slipped past {enemy.name}'s reach and escaped the battle!"
            )
        else:
            # Failed escape: take opportunity attack
            e_variance = random.randint(0, 3)
            e_dmg = max(3, enemy.attack + e_variance - (player.defense // 3))
            player.health = max(0, player.health - e_dmg)
            damage_taken += e_dmg
            details.append(
                f"⚠️ [bold red]Retreat Intercepted![/bold red] {enemy.name} clipped {actor_name} while fleeing for [bold magenta]{e_dmg}[/bold magenta] damage!"
            )

    else:
        # Fallback unknown action
        details.append(f"❓ {actor_name} hesitated ({action}), giving {enemy.name} an opening.")
        e_dmg = max(2, enemy.attack - (player.defense // 2))
        player.health = max(0, player.health - e_dmg)
        damage_taken += e_dmg

    player_died = not player.is_alive()
    if player_died:
        details.append(f"💀 [bold red]{actor_name} has fallen in battle...[/bold red]")

    combat_ended = enemy_defeated or escaped or player_died

    summary = (
        f"Defeated {enemy.name}" if enemy_defeated else
        "Escaped combat" if escaped else
        "Fell in battle" if player_died else
        f"Dealt {damage_dealt} dmg, took {damage_taken} dmg"
    )

    clean_details = [strip_markup(d) for d in details]

    return TurnOutcome(
        summary=summary,
        details=details,
        clean_details=clean_details,
        damage_dealt=damage_dealt,
        damage_taken=damage_taken,
        healing_done=healing_done,
        gold_gained=gold_gained,
        potions_gained=0,
        potions_used=potions_used,
        enemy_defeated=enemy_defeated,
        combat_ended=combat_ended,
        escaped=escaped,
        player_died=player_died,
    )


def resolve_explore(player: JevPlayer, room: Room, decision: ExploreDecision | str) -> TurnOutcome:
    """
    Resolve non-combat exploration (Treasure, Shrine, Trap, Empty).
    Accepts ExploreDecision or string action.
    """
    details: list[str] = []
    gold_gained = 0
    potions_gained = 0
    healing_done = 0
    damage_taken = 0

    is_ai = isinstance(decision, ExploreDecision)
    action = decision.action.upper() if is_ai else str(decision).upper()
    actor_name = "Jev" if is_ai else "You"

    if action == "TAKE_TREASURE":
        gold_gained = room.gold
        player.gold += gold_gained
        details.append(f"💎 {actor_name} opened the treasure chest and claimed [bold yellow]+{gold_gained} gold[/bold yellow]!")
        if room.has_potion:
            player.potions += 1
            potions_gained += 1
            details.append("🧪 Found a glowing [bold magenta]Healing Potion[/bold magenta] inside!")
        room.cleared = True

    elif action == "USE_SHRINE":
        heal_val = min(room.shrine_heal, player.max_health - player.health)
        player.health += heal_val
        healing_done += heal_val
        details.append(
            f"✨ {actor_name} kneeled before the celestial fountain, restoring [bold green]+{heal_val} HP[/bold green] (Health: {player.health}/{player.max_health})."
        )
        room.cleared = True

    elif action == "DISARM_TRAP":
        disarm_success = random.random() < 0.70
        if disarm_success:
            details.append(f"🔧 [bold green]Trap Disarmed:[/bold green] {actor_name} deftly unhooked the tripwire mechanism!")
            if room.gold > 0:
                gold_gained = room.gold
                player.gold += gold_gained
                details.append(f"💰 Recovered [bold yellow]+{gold_gained} gold[/bold yellow] from the disarmed cache.")
        else:
            trap_dmg = room.trap_damage
            player.health = max(0, player.health - trap_dmg)
            damage_taken += trap_dmg
            details.append(
                f"💥 [bold red]Trap Triggered![/bold red] Spikes burst forth, dealing [bold magenta]{trap_dmg}[/bold magenta] damage!"
            )
            if room.gold > 0:
                gold_gained = room.gold
                player.gold += gold_gained
                details.append(f"💰 Snatched [bold yellow]+{gold_gained} gold[/bold yellow] amidst the chaos.")
        room.cleared = True

    elif action == "SEARCH_MORE":
        found_something = False
        if room.gold > 0:
            gold_gained = room.gold
            player.gold += gold_gained
            details.append(f"🔍 {actor_name} searched crevices and found [bold yellow]+{gold_gained} gold[/bold yellow]!")
            found_something = True
        if room.has_potion:
            player.potions += 1
            potions_gained += 1
            details.append("🔍 Hidden in a nook: Found a [bold magenta]Healing Potion[/bold magenta]!")
            found_something = True
        if not found_something:
            details.append(f"🔍 {actor_name} searched the masonry and dust, but found only ancient cobwebs.")
        room.cleared = True

    elif action == "IGNORE":
        details.append(f"🚶 {actor_name} prudently stepped around the room and continued onward.")
        room.cleared = True

    else:
        details.append(f"🚶 {actor_name} surveyed the chamber and pressed forward.")
        room.cleared = True

    player_died = not player.is_alive()
    if player_died:
        details.append(f"💀 [bold red]{actor_name} perished from trap injuries![/bold red]")

    summary = (
        f"Looted {gold_gained} gold" if gold_gained > 0 else
        f"Healed {healing_done} HP" if healing_done > 0 else
        "Explored room"
    )

    clean_details = [strip_markup(d) for d in details]

    return TurnOutcome(
        summary=summary,
        details=details,
        clean_details=clean_details,
        damage_dealt=0,
        damage_taken=damage_taken,
        healing_done=healing_done,
        gold_gained=gold_gained,
        potions_gained=potions_gained,
        potions_used=0,
        enemy_defeated=False,
        combat_ended=True,
        escaped=False,
        player_died=player_died,
    )


def resolve_fork(player: JevPlayer, room: Room, decision: ForkDecision | str) -> TurnOutcome:
    """Resolve crossroads branching navigation."""
    is_ai = isinstance(decision, ForkDecision)
    path = decision.path.upper() if is_ai else str(decision).upper()
    actor_name = "Jev" if is_ai else "You"

    risk_info = f" (Risk Assessment: {decision.risk_score}/10)" if is_ai else ""
    details = [
        f"🧭 [bold cyan]Path Selected:[/bold cyan] {actor_name} chose the [bold yellow]{path}[/bold yellow] corridor{risk_info}."
    ]
    room.cleared = True

    clean_details = [strip_markup(d) for d in details]

    return TurnOutcome(
        summary=f"Chose path: {path}",
        details=details,
        clean_details=clean_details,
        combat_ended=True,
        player_died=False,
    )
