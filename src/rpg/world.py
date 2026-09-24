"""
world.py - Dungeon generation, entities, items, and game world state.
"""

from __future__ import annotations
import copy
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
    description: str
    max_health: int = 0

    def __post_init__(self):
        if self.max_health == 0:
            self.max_health = self.health

    def is_alive(self) -> bool:
        return self.health > 0

    def clone(self) -> Enemy:
        return copy.deepcopy(self)


# Template enemies from PLAN.md
ENEMY_TEMPLATES = [
    Enemy(
        name="Goblin",
        health=30,
        attack=8,
        defense=3,
        reward_gold=10,
        description="A small, quick goblin wielding a rusty jagged dagger."
    ),
    Enemy(
        name="Orc Warrior",
        health=60,
        attack=14,
        defense=6,
        reward_gold=25,
        description="A hulking orc clad in heavy, scarred iron armor."
    ),
    Enemy(
        name="Dark Mage",
        health=40,
        attack=20,
        defense=2,
        reward_gold=35,
        description="A robed dark mage crackling with forbidden chaotic spells."
    ),
    Enemy(
        name="Troll",
        health=80,
        attack=18,
        defense=10,
        reward_gold=40,
        description="A regenerating cave troll with thick stone-like hide."
    ),
    Enemy(
        name="Dragon Boss",
        health=150,
        attack=30,
        defense=15,
        reward_gold=200,
        description="The ancient dungeon dragon — massive, winged, breathing incandescent fury."
    ),
]


@dataclass
class Room:
    room_type: RoomType
    name: str
    description: str
    enemy: Enemy | None = None
    gold: int = 0
    has_potion: bool = False
    trap_damage: int = 0
    shrine_heal: int = 0
    exits: list[str] = field(default_factory=list)
    cleared: bool = False


@dataclass
class JevPlayer:
    health: int = 100
    max_health: int = 100
    attack: int = 15
    defense: int = 10
    potions: int = 2
    gold: int = 0
    floor: int = 1
    current_room_index: int = 0
    rooms_cleared: int = 0
    total_turns: int = 0
    kills: int = 0

    def is_alive(self) -> bool:
        return self.health > 0


ROOM_THEMES_BY_FLOOR = {
    1: [
        ("Damp Dungeon Entrance", "Mossy cobblestones slick with moisture; distant water droplets echo."),
        ("Forgotten Armory", "Racks of rusted spears and broken bucklers litter the floor."),
        ("Guard Outpost", "An abandoned checkpoint with extinguished braziers and splintered tables."),
        ("Cobwebbed Vault", "Heavy oak beams sag beneath centuries of spiderwebs."),
    ],
    2: [
        ("Crypt of the Forgotten", "Crumbling stone sarcophagi line the walls in silent vigil."),
        ("Chasm Overlook", "A narrow stone ledge hugging a sheer drop into pitch blackness."),
        ("Flooded Cellar", "Ankle-deep murky water hiding submerged debris and slippery stones."),
        ("Bone Altar", "A sacrificial dais surrounded by glowing phosphorescent mushrooms."),
    ],
    3: [
        ("The Molten Anvil", "Heat wafts from iron vents; sulfurous soot dusts the walkway."),
        ("Catacombs of Whispers", "Pillars adorned with demonic carvings that seem to hum softly."),
        ("Ruined Laboratory", "Shattered alchemical vials give off a faint, pungent vapor."),
        ("Obsidian Corridor", "Polished black volcanic glass walls reflecting twisted silhouettes."),
    ],
    4: [
        ("Sanctum of Shadows", "A grand hall where torch flames burn cold azure."),
        ("The Iron Gauntlet", "Reinforced iron archways scarred by claw marks and scorch lines."),
        ("Hall of Heroes", "Beheaded statues of ancient knights standing in silent condemnation."),
        ("Abyssal Threshold", "The air grows heavy, vibrating with ominous magical pressure."),
    ],
    5: [
        ("Wyrm's Ascent", "A cavernous stairway blasted directly out of molten magma rock."),
        ("Hoard Ante-Chamber", "Mounds of charred bones and fused coins surround giant claw prints."),
        ("Inner Dragon Sanctum", "The apex of the dungeon: a colossal vault filled with ash and embers where the dragon reigns."),
    ],
}


def create_room(floor: int, room_type: RoomType, is_final_boss: bool = False) -> Room:
    """Generate a single room with balanced contents."""
    themes = ROOM_THEMES_BY_FLOOR.get(floor, ROOM_THEMES_BY_FLOOR[1])
    name, base_desc = random.choice(themes)

    if is_final_boss or room_type == RoomType.BOSS:
        boss = copy.deepcopy(ENEMY_TEMPLATES[4])  # Dragon Boss
        return Room(
            room_type=RoomType.BOSS,
            name="The Ancient Dragon's Lair",
            description=f"A vast obsidian cavern radiating scorching heat. {boss.description}",
            enemy=boss,
            gold=boss.reward_gold,
            has_potion=True,
            cleared=False,
        )

    if room_type == RoomType.ENEMY:
        # Scale enemy selection by floor
        if floor == 1:
            template = ENEMY_TEMPLATES[0]  # Goblin
        elif floor == 2:
            template = random.choice([ENEMY_TEMPLATES[0], ENEMY_TEMPLATES[1]])  # Goblin or Orc
        elif floor == 3:
            template = random.choice([ENEMY_TEMPLATES[1], ENEMY_TEMPLATES[2]])  # Orc or Mage
        else:
            template = random.choice([ENEMY_TEMPLATES[2], ENEMY_TEMPLATES[3]])  # Mage or Troll

        enemy = template.clone()
        return Room(
            room_type=RoomType.ENEMY,
            name=name,
            description=f"{base_desc} In the center stands an enemy: {enemy.description}",
            enemy=enemy,
            gold=enemy.reward_gold,
            has_potion=(random.random() < 0.25),
            cleared=False,
        )

    elif room_type == RoomType.TREASURE:
        gold_reward = random.randint(25, 60) * floor
        has_pot = random.random() < 0.65
        return Room(
            room_type=RoomType.TREASURE,
            name=f"Vault - {name}",
            description=f"{base_desc} An ornate gilded chest rests on a stone pedestal.",
            gold=gold_reward,
            has_potion=has_pot,
            cleared=False,
        )

    elif room_type == RoomType.SHRINE:
        heal_amt = random.randint(35, 60)
        return Room(
            room_type=RoomType.SHRINE,
            name=f"Shrine - {name}",
            description=f"{base_desc} A luminous fountain radiates soothing celestial light.",
            shrine_heal=heal_amt,
            cleared=False,
        )

    elif room_type == RoomType.TRAP:
        trap_dmg = random.randint(12, 22) + (floor * 3)
        return Room(
            room_type=RoomType.TRAP,
            name=f"Perilous Passage - {name}",
            description=f"{base_desc} Floor pressure plates and concealed darts threaten unwary adventurers.",
            trap_damage=trap_dmg,
            gold=random.randint(10, 30),
            cleared=False,
        )

    elif room_type == RoomType.FORK:
        return Room(
            room_type=RoomType.FORK,
            name=f"Crossroads - {name}",
            description=f"{base_desc} The stone corridor splits into distinct pathways ahead.",
            exits=["LEFT", "RIGHT", "BACK"],
            cleared=False,
        )

    else:  # EMPTY
        found_gold = random.randint(5, 15) if random.random() < 0.4 else 0
        return Room(
            room_type=RoomType.EMPTY,
            name=name,
            description=f"{base_desc} The chamber is eerie and still. No obvious foes are in sight.",
            gold=found_gold,
            has_potion=(random.random() < 0.2),
            cleared=False,
        )


class Dungeon:
    def __init__(self, total_floors: int = 5, rooms_per_floor: tuple[int, int] = (3, 4)):
        self.total_floors = total_floors
        self.rooms_per_floor = rooms_per_floor
        self.floors: list[list[Room]] = []
        self.generate_dungeon()

    def generate_dungeon(self):
        self.floors = []
        possible_middle_types = [
            RoomType.ENEMY,
            RoomType.TREASURE,
            RoomType.SHRINE,
            RoomType.TRAP,
            RoomType.FORK,
            RoomType.ENEMY,  # weighted higher
        ]

        for floor_num in range(1, self.total_floors + 1):
            floor_rooms: list[Room] = []
            num_rooms = random.randint(self.rooms_per_floor[0], self.rooms_per_floor[1])

            if floor_num == self.total_floors:
                # Final floor: 2 rooms before the boss room
                floor_rooms.append(create_room(floor_num, RoomType.TREASURE))
                floor_rooms.append(create_room(floor_num, RoomType.ENEMY))
                floor_rooms.append(create_room(floor_num, RoomType.BOSS, is_final_boss=True))
            else:
                # First room is usually enemy or empty
                first_type = random.choice([RoomType.ENEMY, RoomType.EMPTY])
                floor_rooms.append(create_room(floor_num, first_type))

                # Middle rooms
                for _ in range(num_rooms - 2):
                    rtype = random.choice(possible_middle_types)
                    floor_rooms.append(create_room(floor_num, rtype))

                # Last room of non-final floors is a challenging encounter or shrine/treasure
                last_type = random.choice([RoomType.ENEMY, RoomType.SHRINE, RoomType.TREASURE])
                floor_rooms.append(create_room(floor_num, last_type))

            self.floors.append(floor_rooms)

    def get_room(self, floor: int, room_idx: int) -> Room | None:
        if 1 <= floor <= len(self.floors):
            f_rooms = self.floors[floor - 1]
            if 0 <= room_idx < len(f_rooms):
                return f_rooms[room_idx]
        return None

    def total_rooms_on_floor(self, floor: int) -> int:
        if 1 <= floor <= len(self.floors):
            return len(self.floors[floor - 1])
        return 0
