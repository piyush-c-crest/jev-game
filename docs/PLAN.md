# 🎮 Jev Plays the Game — Implementation Plan

## Goal Description

Build a **dungeon RPG** where **Jev (TypeSafe AI's System One model) IS the player**. The game runs autonomously, presenting each situation to Jev, which then makes all decisions — move, fight, flee, use items, explore — and we watch it play turn-by-turn with full transparency into its reasoning and confidence scores.

The output is a **rich, animated terminal UI** (using `rich`) that shows:
- The current dungeon room and its contents
- The live game state (health, inventory, floor level)
- Jev's "thinking" — the questions asked and answers received
- The chosen action and its outcome
- A running log of Jev's adventure

**Why this is cool:** Jev doesn't generate text — it makes *fast, structured decisions with confidence scores*. So instead of a chatty AI player, you see a crisp, deterministic brain deciding: `ATTACK (87% confident)`, `Threat: 8.2/10`, `Use Potion? Yes (92%)`. It feels like watching a real AI think.

> **NOTE:** API Key is stored in `.env` and never hardcoded into source files.

---

## Architecture Overview

```
Game Loop (game_loop.py)
    │
    ▼
State Builder (state_builder.py)
    │  Natural language context string
    ▼
Jev Decision Engine (jev_engine.py)
    │  TypeSafe API Call
    ▼
Jev Model (typesafe.ai)
    │  Choice + Score + Noul results
    ▼
Action Resolver (action_resolver.py)
    │  Outcome + new game state
    ▼
World Engine (world.py)
    │  Updated state
    ▼
Terminal UI (ui.py — rich)
```

---

## Game Design

### The Dungeon

- A procedurally-generated dungeon of **5 floors**, each with **3–5 rooms**
- Each room can contain: **enemies**, **treasure chests**, **healing shrines**, **traps**, or be **empty**
- Jev wins by reaching **Floor 5, Room: Boss** and defeating the final boss
- Jev loses if its health drops to 0

### Jev's Stats

| Stat | Starting Value |
|------|---------------|
| ❤️ Health | 100 |
| ⚔️ Attack Power | 15 |
| 🛡️ Defense | 10 |
| 🧪 Potions | 2 |
| 💰 Gold | 0 |

### Jev's Decision Points

Every turn, Jev is asked **4–6 questions in one API call** depending on the room type:

**In a room with an enemy:**

| Question | Type | Options/Range |
|----------|------|---------------|
| What should I do? | `Choice` | ATTACK, FLEE, USE_POTION, DEFEND |
| How dangerous is this enemy? | `Score` | 0–10 |
| Should I use a potion before attacking? | `Noul` | Yes/No probability |
| Is fleeing worth it? | `Noul` | Yes/No probability |

**In a room with treasure/shrine:**

| Question | Type | Options/Range |
|----------|------|---------------|
| What should I do here? | `Choice` | TAKE_TREASURE, USE_SHRINE, IGNORE, SEARCH_MORE |
| How valuable does this seem? | `Score` | 0–10 |

**At a fork (multiple paths):**

| Question | Type | Options/Range |
|----------|------|---------------|
| Which path should I take? | `Choice` | LEFT, RIGHT, BACK |
| How risky does the chosen path feel? | `Score` | 0–10 |

---

## Project Structure

```
jev-game/
├── .env                    # TYPESAFE_API_KEY (never committed)
├── .gitignore
├── README.md
├── PLAN.md                 # This file
├── requirements.txt
├── main.py                 # Entry point — starts the game
├── game_loop.py            # Core game loop (turn engine)
├── world.py                # Dungeon generation, rooms, enemies, items
├── jev_engine.py           # Jev API wrapper + all question sets
├── state_builder.py        # Converts game state → natural language for Jev
├── action_resolver.py      # Maps Jev decisions → game outcomes
└── ui.py                   # Rich terminal UI rendering
```

---

## Proposed Changes (Files to Build)

### Component 1: Project Setup

**`requirements.txt`**
```
typesafe-sdk>=0.3.0
python-dotenv>=1.0.0
rich>=13.7.0
pydantic>=2.7.0
```

**`.env`** ✅ Already created
```
TYPESAFE_API_KEY=<your-key>
```

**`.gitignore`** ✅ Already created

---

### Component 2: World Engine — `world.py`

Handles dungeon generation, all game entities (enemies, items, rooms), and combat math.

**Key classes:**
```python
from dataclasses import dataclass, field
from enum import Enum
import random

class RoomType(Enum):
    EMPTY = "empty"
    ENEMY = "enemy"
    TREASURE = "treasure"
    SHRINE = "shrine"
    TRAP = "trap"
    BOSS = "boss"
    FORK = "fork"

@dataclass
class Enemy:
    name: str
    health: int
    attack: int
    defense: int
    reward_gold: int
    description: str  # Passed to Jev as context

@dataclass
class Room:
    room_type: RoomType
    description: str
    enemy: Enemy | None = None
    gold: int = 0
    has_potion: bool = False
    exits: list[str] = field(default_factory=list)

@dataclass
class JevPlayer:
    health: int = 100
    max_health: int = 100
    attack: int = 15
    defense: int = 10
    potions: int = 2
    gold: int = 0
    floor: int = 1
    rooms_cleared: int = 0
    total_turns: int = 0

ENEMIES = [
    Enemy("Goblin",      health=30,  attack=8,  defense=3,  reward_gold=10,  description="A small, quick goblin with a rusty dagger"),
    Enemy("Orc Warrior", health=60,  attack=14, defense=6,  reward_gold=25,  description="A hulking orc in heavy armour"),
    Enemy("Dark Mage",   health=40,  attack=20, defense=2,  reward_gold=35,  description="A robed mage casting dark spells"),
    Enemy("Troll",       health=80,  attack=18, defense=10, reward_gold=40,  description="A regenerating troll with thick hide"),
    Enemy("Dragon Boss", health=150, attack=30, defense=15, reward_gold=200, description="The ancient dungeon dragon — final boss"),
]
```

---

### Component 3: State Builder — `state_builder.py`

Converts structured game state into rich natural language context strings that Jev reads as its "world view".

```python
def build_combat_context(player, enemy, room) -> str:
    return (
        f"I am Jev, an adventurer on floor {player.floor} of a dangerous dungeon. "
        f"I am in a {room.description}. "
        f"My health is {player.health}/{player.max_health}. "
        f"I have {player.potions} healing potions and {player.gold} gold. "
        f"I am facing: {enemy.description}. "
        f"The enemy has approximately {enemy.health} HP and deals {enemy.attack} damage. "
        f"My attack power is {player.attack} and my defense is {player.defense}. "
        f"I have cleared {player.rooms_cleared} rooms so far."
    )
```

---

### Component 4: Jev Decision Engine — `jev_engine.py`

The heart of the project. All 3 question set types (combat, explore, fork) sent to Jev.

```python
def jev_combat_decision(context: str) -> CombatDecision:
    """Ask Jev what to do in combat — all 4 questions in ONE API call."""
    response = client.system_one(
        state=context,
        questions={
            "action": Choice(
                instructions="What should I do this combat turn?",
                criteria={
                    "ATTACK":     "Strike the enemy with my weapon",
                    "FLEE":       "Run away from this fight",
                    "USE_POTION": "Drink a healing potion (only if I have one)",
                    "DEFEND":     "Take a defensive stance to reduce incoming damage",
                }
            ),
            "threat_level": Score(
                instructions="On a scale of 0-10, how dangerous is this enemy to me right now?",
                min=0, max=10
            ),
            "use_potion_first": Noul(
                instructions="Should I drink a healing potion before my main action?"
            ),
            "flee_worth_it": Noul(
                instructions="Is fleeing this fight worth the risk of being caught?"
            ),
        }
    )
```

---

### Component 5: Action Resolver — `action_resolver.py`

Processes Jev's decision and applies it to the game world with randomized combat outcomes.

```python
def resolve_combat(player, enemy, decision) -> TurnOutcome:
    match decision.action:
        case "ATTACK":     # deal damage, take counter-attack
        case "FLEE":       # 60% escape chance, else take damage
        case "USE_POTION": # heal 40 HP, still take damage
        case "DEFEND":     # take halved damage
```

---

### Component 6: Terminal UI — `ui.py`

Rich 2-panel terminal layout:

```
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│  🗺️  DUNGEON  —  Floor 3, Room 2     │  │  🧠 JEV IS THINKING...       │
│                                      │  │                              │
│  [ASCII art dungeon room]            │  │  Action?   → ATTACK  (87%)   │
│                                      │  │  Threat?   → 7.4 / 10        │
│  A hulking Orc Warrior blocks        │  │  Potion?   → No  (23%)       │
│  your path...                        │  │  Flee?     → No  (18%)       │
│                                      │  │                              │
│  ❤️  Jev HP:  [████████░░] 82/100    │  │  ✅ DECISION: ATTACK          │
│  ⚔️  Orc HP:  [████░░░░░░] 40/60     │  └──────────────────────────────┘
│  🧪 Potions: 2   💰 Gold: 35         │
└──────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│  📜 ADVENTURE LOG                                                       │
│  Turn 7 │ Jev strikes for 12! Orc counter-attacks for 8.               │
│  Turn 6 │ Jev enters a torch-lit chamber. An Orc Warrior appears!       │
└─────────────────────────────────────────────────────────────────────────┘
```

**`rich` components used:**
- `Layout` — splits screen into panels
- `Panel` — bordered sections
- `Progress` — health bars
- `Table` — Jev's thinking display
- `Spinner` — shows while waiting for Jev API call
- `Console` markup for colors

---

### Component 7: Game Loop + Entry Point

**`game_loop.py`** — Turn engine:
For each room → get context → call Jev → show thinking → resolve action → render outcome → repeat.

**`main.py`**
```python
from game_loop import run_game
if __name__ == "__main__":
    run_game()
```

---

## Verification Plan

### Run the game

```powershell
# Install dependencies
pip install -r requirements.txt

# Verify Jev API connection
python -c "from jev_engine import client; print('Jev connected')"

# Run the game!
python main.py
```

### Manual Verification Checklist

- [ ] Combat decisions make sense — low-health Jev uses potions more often
- [ ] Threat scores correlate — boss fight shows 8–10/10 threat level
- [ ] Confidence scores vary — easy rooms yield higher confidence
- [ ] Both win/lose outcomes reachable across multiple runs
- [ ] Terminal UI is readable — health bars update, adventure log scrolls
- [ ] API key never appears in source code — only in `.env`

---

## Timeline Estimate

| # | File | Purpose | Est. |
|---|------|---------|------|
| 1 | Setup files | `requirements.txt`, `.env`, `.gitignore` | ✅ Done |
| 2 | `world.py` | Dungeon + entities + combat math | 20 min |
| 3 | `state_builder.py` | Context strings for Jev | 10 min |
| 4 | `jev_engine.py` | Jev API + all 3 question sets | 20 min |
| 5 | `action_resolver.py` | Game outcome logic | 15 min |
| 6 | `ui.py` | Rich terminal UI | 25 min |
| 7 | `game_loop.py` + `main.py` | Turn engine + entry point | 17 min |
| **Total** | | | **~1.75 hrs** |
