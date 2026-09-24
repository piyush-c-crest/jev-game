"""
ui.py - Rich terminal interface for Jev Plays the Game.
Provides a 2-panel live layout, ASCII art, health bars, Jev thinking tables, and adventure log.
"""

from __future__ import annotations
import sys
from typing import Any

# Ensure UTF-8 output encoding across Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .world import JevPlayer, Room, Enemy, RoomType
from .jev_engine import CombatDecision, ExploreDecision, ForkDecision

console = Console(highlight=False)

# Compact ASCII Art for entities and rooms
ASCII_ART = {
    "Goblin": (
        "    (o.o)   \n"
        "   /|   |\\  \n"
        "   / \\ / \\  \n"
        "  [Rusty Dagger]"
    ),
    "Orc Warrior": (
        "   <[o_o]>  \n"
        "  ==|###|== \n"
        "   /|   |\\  \n"
        "  [Heavy Cleaver]"
    ),
    "Dark Mage": (
        "    /\\^/\\   \n"
        "   ( -.- )  \n"
        "   /| * |\\  \n"
        "  [Dark Grimoire]"
    ),
    "Troll": (
        "   /{O_O}\\  \n"
        "  //|###|\\\\ \n"
        "  ( |   | ) \n"
        "  [Stone Club]"
    ),
    "Dragon Boss": (
        "   /\\__/\\   /\\__/\\  \n"
        "  (  o.o )-( o.o  ) \n"
        "  <(  \"\"\"   \"\"\"  )> \n"
        "   /====[FIRE]====\\ \n"
        "  [ANCIENT DRAGON]"
    ),
    "treasure": (
        "  .--------------.  \n"
        "  |  [========]  |  \n"
        "  |  |  $$$   |  |  \n"
        "  '--------------'  "
    ),
    "shrine": (
        "       /\\       \n"
        "      <++>      \n"
        "     /    \\     \n"
        "   [~~~REST~~~] "
    ),
    "trap": (
        "   /\\  /\\  /\\   \n"
        "  |  ||  ||  |  \n"
        "  ^^^^^^^^^^^^  \n"
        "  [TRIPWIRE SPIKES]"
    ),
    "fork": (
        "       ||       \n"
        "   <===||===>   \n"
        "       ||       \n"
        "  [CROSSROADS]  "
    ),
    "empty": (
        "   . . . . . .  \n"
        "  :   SILENT   :\n"
        "   ' ' ' ' ' '  \n"
        "  [DESOLATE HALL]"
    ),
}


def get_health_bar(current: int, max_val: int, width: int = 15) -> str:
    """Generate a colored progress bar representation of health."""
    current = max(0, min(current, max_val))
    ratio = current / max(1, max_val)
    filled = int(ratio * width)
    empty = width - filled

    if ratio < 0.30:
        color = "bold red"
    elif ratio < 0.60:
        color = "bold yellow"
    else:
        color = "bold green"

    bar = "█" * filled + "░" * empty
    return f"[{color}][{bar}][/{color}] {current}/{max_val}"


def get_confidence_badge(confidence: float) -> str:
    """Format confidence score with visual color tier."""
    pct = int(confidence * 100)
    if pct >= 80:
        return f"[bold green]{pct}%[/bold green]"
    elif pct >= 60:
        return f"[bold yellow]{pct}%[/bold yellow]"
    else:
        return f"[bold red]{pct}%[/bold red]"


def build_dungeon_panel(player: JevPlayer, room: Room, total_rooms: int) -> Panel:
    """Construct the left panel: Dungeon room, ASCII art, and Player/Enemy stats."""
    if room.enemy and room.enemy.is_alive():
        art = ASCII_ART.get(room.enemy.name, ASCII_ART["Goblin"])
    elif room.room_type == RoomType.TREASURE:
        art = ASCII_ART["treasure"]
    elif room.room_type == RoomType.SHRINE:
        art = ASCII_ART["shrine"]
    elif room.room_type == RoomType.TRAP:
        art = ASCII_ART["trap"]
    elif room.room_type == RoomType.FORK:
        art = ASCII_ART["fork"]
    else:
        art = ASCII_ART["empty"]

    header = f"[bold cyan]Floor {player.floor}/5[/bold cyan]  •  [bold yellow]Room {player.current_room_index + 1}/{total_rooms}[/bold yellow]  •  [bold magenta]{room.name}[/bold magenta]"

    player_hp = get_health_bar(player.health, player.max_health)
    status_lines = [
        f"❤️  [bold white]Jev HP :[/bold white] {player_hp}",
    ]

    if room.enemy and room.enemy.is_alive():
        enemy_hp = get_health_bar(room.enemy.health, room.enemy.max_health)
        status_lines.append(f"⚔️  [bold red]{room.enemy.name:7}:[/bold red] {enemy_hp}")
    else:
        status_lines.append("⚔️  [dim italic]No hostile entities present[/dim italic]")

    inv_line = (
        f"🧪 [bold magenta]Potions: {player.potions}[/bold magenta]   "
        f"💰 [bold yellow]Gold: {player.gold}[/bold yellow]   "
        f"⚔️ [bold white]Atk: {player.attack}[/bold white]   "
        f"🛡️ [bold white]Def: {player.defense}[/bold white]   "
        f"💀 [bold red]Kills: {player.kills}[/bold red]"
    )

    body = (
        f"{header}\n\n"
        f"[dim]{room.description}[/dim]\n\n"
        f"[bold bright_blue]{art}[/bold bright_blue]\n\n"
        + "\n".join(status_lines)
        + f"\n\n{inv_line}"
    )

    return Panel(
        body,
        title="[bold yellow]🗺️  DUNGEON CHAMBER[/bold yellow]",
        border_style="bright_blue",
        box=box.ROUNDED,
    )


def build_thinking_panel(decision: Any) -> Panel:
    """Construct the right panel: Jev's questions, structured scores, and decisions."""
    if not decision:
        return Panel(
            "[dim italic]Awaiting Jev's System One query...[/dim italic]",
            title="[bold cyan]🧠 JEV'S SYSTEM ONE REASONING[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
        )

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Question / Primitive", style="white", ratio=4)
    table.add_column("Jev's Answer", style="bold yellow", ratio=3)
    table.add_column("Conf.", justify="right", ratio=2)

    fallback_badge = " [bold red](FALLBACK)[/bold red]" if getattr(decision, "is_fallback", False) else ""
    latency = getattr(decision, "latency_ms", 0.0)

    if isinstance(decision, CombatDecision):
        table.add_row(
            "Action to take? (Choice)",
            f"[bold green]{decision.action}[/bold green]",
            get_confidence_badge(decision.action_confidence),
        )
        threat_color = "red" if decision.threat_level >= 7.0 else "yellow" if decision.threat_level >= 4.0 else "green"
        table.add_row(
            "Threat level? (Score 0-10)",
            f"[{threat_color}]{decision.threat_level:.1f} / 10[/{threat_color}]",
            get_confidence_badge(decision.threat_confidence),
        )
        potion_pct = int(decision.use_potion_first_prob * 100)
        table.add_row(
            "Use potion first? (Noul)",
            f"{'Yes' if potion_pct >= 50 else 'No'} ({potion_pct}%)",
            "—",
        )
        flee_pct = int(decision.flee_worth_it_prob * 100)
        table.add_row(
            "Is fleeing worth it? (Noul)",
            f"{'Yes' if flee_pct >= 50 else 'No'} ({flee_pct}%)",
            "—",
        )
        chosen_summary = f"[bold green]{decision.action}[/bold green]"

    elif isinstance(decision, ExploreDecision):
        table.add_row(
            "What to do? (Choice)",
            f"[bold green]{decision.action}[/bold green]",
            get_confidence_badge(decision.action_confidence),
        )
        table.add_row(
            "Value score? (Score 0-10)",
            f"[bold cyan]{decision.value_score:.1f} / 10[/bold cyan]",
            get_confidence_badge(decision.value_confidence),
        )
        safe_pct = int(decision.safe_to_interact_prob * 100)
        table.add_row(
            "Safe to interact? (Noul)",
            f"{'Yes' if safe_pct >= 50 else 'No'} ({safe_pct}%)",
            "—",
        )
        chosen_summary = f"[bold green]{decision.action}[/bold green]"

    elif isinstance(decision, ForkDecision):
        table.add_row(
            "Which corridor? (Choice)",
            f"[bold green]{decision.path}[/bold green]",
            get_confidence_badge(decision.path_confidence),
        )
        table.add_row(
            "Risk rating? (Score 0-10)",
            f"[bold red]{decision.risk_score:.1f} / 10[/bold red]",
            get_confidence_badge(decision.risk_confidence),
        )
        chosen_summary = f"Advance [bold yellow]{decision.path}[/bold yellow]"

    else:
        chosen_summary = "WAIT"

    footer_text = (
        f"\n⚡ [dim]Latency: [bold white]{latency:.0f} ms[/bold white][/dim]{fallback_badge}\n"
        f"🎯 [bold white]Final Execution:[/bold white] {chosen_summary}"
    )

    panel_content = Group(table, Text.from_markup(footer_text))

    return Panel(
        panel_content,
        title="[bold cyan]🧠 JEV'S SYSTEM ONE REASONING[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    )


def build_log_panel(logs: list[str], max_entries: int = 7) -> Panel:
    """Construct the bottom panel: scrolling Adventure Log."""
    recent_logs = logs[-max_entries:] if logs else ["[dim]The dungeon awaits Jev's first step...[/dim]"]
    log_text = "\n".join(recent_logs)

    return Panel(
        log_text,
        title="[bold green]📜 ADVENTURE CHRONICLES[/bold green]",
        border_style="green",
        box=box.ROUNDED,
    )


def render_game_screen(
    player: JevPlayer,
    room: Room,
    total_rooms: int,
    decision: Any,
    logs: list[str],
):
    """Render the full composite game screen."""
    layout = Layout()
    layout.split_column(
        Layout(name="top", ratio=3),
        Layout(name="bottom", ratio=1),
    )
    layout["top"].split_row(
        Layout(name="dungeon", ratio=5),
        Layout(name="brain", ratio=5),
    )

    layout["dungeon"].update(build_dungeon_panel(player, room, total_rooms))
    layout["brain"].update(build_thinking_panel(decision))
    layout["bottom"].update(build_log_panel(logs))

    console.clear()
    console.print(layout)


def display_intro_banner():
    """Display welcome banner at game start."""
    console.clear()
    title = (
        "[bold cyan]╔══════════════════════════════════════════════════════════════════════════════╗[/bold cyan]\n"
        "[bold cyan]║[/bold cyan]                         [bold yellow]🎮  JEV PLAYS THE GAME  🎮[/bold yellow]                           [bold cyan]║[/bold cyan]\n"
        "[bold cyan]║[/bold cyan]               [dim]An Autonomous Dungeon Crawler Powered by TypeSafe AI[/dim]          [bold cyan]║[/bold cyan]\n"
        "[bold cyan]╚══════════════════════════════════════════════════════════════════════════════╝[/bold cyan]\n"
    )
    console.print(title)
    console.print(
        "[white]Watch [bold cyan]Jev (System One AI)[/bold cyan] explore a 5-floor dungeon autonomously,\n"
        "evaluating situations with [bold green]Choice[/bold green], [bold yellow]Score[/bold yellow], and [bold magenta]Noul[/bold magenta] structured primitives!\n\n"
        "⚔️  Objective: Reach Floor 5 and defeat the Ancient Dragon Boss!\n"
        "❤️  Defeat Condition: Jev's HP drops to 0.\n[/white]"
    )


def display_victory_screen(player: JevPlayer, total_turns: int):
    """Celebratory victory screen when Jev slays the Dragon Boss."""
    console.print("\n")
    win_panel = Panel(
        f"[bold yellow]🏆 ✨ VICTORY ACHIEVED! ✨ 🏆[/bold yellow]\n\n"
        f"[bold green]Jev has defeated the Ancient Dragon Boss and conquered the Dungeon![/bold green]\n\n"
        f"📊 [bold white]Final Adventure Stats:[/bold white]\n"
        f"  • Total Turns Elapsed : [bold cyan]{total_turns}[/bold cyan]\n"
        f"  • Monsters Slain      : [bold red]{player.kills}[/bold red]\n"
        f"  • Chambers Cleared    : [bold yellow]{player.rooms_cleared}[/bold yellow]\n"
        f"  • Gold Hoarded        : [bold yellow]{player.gold} Gold[/bold yellow]\n"
        f"  • Final Health        : [bold green]{player.health}/{player.max_health} HP[/bold green]\n"
        f"  • Potions Remaining   : [bold magenta]{player.potions}[/bold magenta]\n\n"
        f"[italic cyan]TypeSafe AI's Jev model made all tactical decisions autonomously![/italic cyan]",
        title="[bold yellow]★ LEGENDARY CONQUEROR ★[/bold yellow]",
        border_style="yellow",
        box=box.DOUBLE,
    )
    console.print(win_panel)


def display_game_over_screen(player: JevPlayer, total_turns: int, last_cause: str):
    """Game over screen when Jev falls in battle."""
    console.print("\n")
    loss_panel = Panel(
        f"[bold red]💀 GAME OVER — JEV HAS FALLEN 💀[/bold red]\n\n"
        f"[dim]{last_cause}[/dim]\n\n"
        f"📊 [bold white]Final Adventure Stats:[/bold white]\n"
        f"  • Floor Reached       : [bold magenta]Floor {player.floor}/5[/bold magenta]\n"
        f"  • Total Turns Lived   : [bold cyan]{total_turns}[/bold cyan]\n"
        f"  • Monsters Slain      : [bold red]{player.kills}[/bold red]\n"
        f"  • Chambers Cleared    : [bold yellow]{player.rooms_cleared}[/bold yellow]\n"
        f"  • Gold Collected      : [bold yellow]{player.gold} Gold[/bold yellow]\n\n"
        f"[italic red]Even the sharpest minds face peril in the deep dark...[/italic red]",
        title="[bold red]REST IN PEACE[/bold red]",
        border_style="red",
        box=box.DOUBLE,
    )
    console.print(loss_panel)
