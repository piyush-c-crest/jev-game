"""
mario_level.py - Super Mario Level Generator with Classic & Kaizo Extreme Modes.
Features treacherous platforming, precision pits, low-ceiling traps, dense enemy formations,
and intense Kaizo obstacles.
"""

from typing import Dict, List, Any


def get_classic_level() -> Dict[str, Any]:
    """Generate original classic World 1-1 layout."""
    rows = 15
    cols = 212
    grid = [[0 for _ in range(cols)] for _ in range(rows)]

    # Ground level: rows 13 and 14
    pits = {69, 70, 86, 87, 88, 153, 154}
    for c in range(cols):
        if c not in pits:
            grid[13][c] = 1
            grid[14][c] = 1

    def place_pipe(start_col: int, height_in_tiles: int):
        top_row = 13 - height_in_tiles
        grid[top_row][start_col] = 6
        grid[top_row][start_col + 1] = 7
        for r in range(top_row + 1, 13):
            grid[r][start_col] = 8
            grid[r][start_col + 1] = 9

    place_pipe(28, 2)
    place_pipe(38, 3)
    place_pipe(46, 4)
    place_pipe(57, 4)
    place_pipe(163, 2)
    place_pipe(179, 2)

    grid[9][16] = 3
    grid[9][20] = 2
    grid[9][21] = 4
    grid[9][22] = 2
    grid[9][23] = 3
    grid[9][24] = 2
    grid[5][22] = 3
    grid[9][64] = 4

    for c in range(77, 80):
        grid[9][c] = 2
    for c in range(80, 88):
        grid[5][c] = 2
    grid[9][80] = 2
    grid[9][81] = 3
    grid[9][82] = 2

    # Staircases
    for step in range(4):
        c = 134 + step
        for r in range(12 - step, 13):
            grid[r][c] = 16
    for step in range(4):
        c = 140 + step
        for r in range(9 + step, 13):
            grid[r][c] = 16
    for step in range(4):
        c = 148 + step
        for r in range(12 - step, 13):
            grid[r][c] = 16
    for step in range(4):
        c = 155 + step
        for r in range(9 + step, 13):
            grid[r][c] = 16
    for step in range(8):
        c = 181 + step
        for r in range(12 - step, 13):
            grid[r][c] = 16
    for r in range(5, 13):
        grid[r][189] = 16

    # Flagpole & Castle
    grid[12][198] = 12
    for r in range(3, 12):
        grid[r][198] = 11
    grid[2][198] = 10

    for r in range(8, 13):
        for c in range(202, 208):
            grid[r][c] = 13
    grid[11][204] = 14
    grid[12][204] = 14
    for c in range(202, 208, 2):
        grid[7][c] = 15

    enemies = [
        {"type": "goomba", "x": 22 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 40 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 51 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 53 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 80 * 16, "y": 4 * 16},
        {"type": "goomba", "x": 82 * 16, "y": 4 * 16},
        {"type": "goomba", "x": 97 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 99 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 107 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 114 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 116 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 125 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 127 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 174 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 176 * 16, "y": 12 * 16},
    ]

    coins = [
        {"x": 16 * 16 + 8, "y": 7 * 16},
        {"x": 22 * 16 + 8, "y": 3 * 16},
        {"x": 33 * 16 + 8, "y": 10 * 16},
        {"x": 81 * 16 + 8, "y": 3 * 16},
        {"x": 109 * 16 + 8, "y": 7 * 16},
    ]

    return {
        "world": "1-1 (NORMAL)",
        "difficulty": "normal",
        "time": 400,
        "rows": rows,
        "cols": cols,
        "tile_size": 16,
        "pixel_width": cols * 16,
        "pixel_height": rows * 16,
        "grid": grid,
        "coins": coins,
        "enemies": enemies,
        "scenery": [
            {"type": "cloud", "x": 8 * 16, "y": 3 * 16},
            {"type": "hill", "x": 0 * 16, "y": 11 * 16},
            {"type": "bush", "x": 11 * 16, "y": 12 * 16},
            {"type": "cloud", "x": 56 * 16, "y": 2 * 16},
            {"type": "hill", "x": 96 * 16, "y": 11 * 16},
        ],
        "spawn": {"x": 3 * 16, "y": 12 * 16},
        "flagpole": {"col": 198, "top_row": 2, "base_row": 12},
        "castle": {"x": 202 * 16, "door_x": 204 * 16 + 8},
    }


def get_extreme_level() -> Dict[str, Any]:
    """
    Generate Kaizo Extreme World 8-4.
    Features:
      - 8 deadly chasms with 1-tile floating stepping stones
      - Low-ceiling jump traps that punish reckless hopping
      - Dense Goomba battalions & narrow Koopa shell bounce corridors
      - Precision stair jumps with gaps
      - Intense 200s countdown timer
    """
    rows = 15
    cols = 212
    grid = [[0 for _ in range(cols)] for _ in range(rows)]

    # Ground level: rows 13 and 14
    # Massive chasm zones:
    # Gap 1: 18-23 (Single-tile step at col 20)
    # Gap 2: 34-37 (Between tall pipes)
    # Gap 3: 48-68 (THE GREAT CHASM: 20 tiles abyss with isolated step stones!)
    # Gap 4: 86-90 (Low-ceiling tunnel exit pit)
    # Gap 5: 104-107 (Pipe corridor death trap)
    # Gap 6: 125-129 (Stepping stone leap)
    # Gap 7: 157-164 (Abyss after staircase of doom)
    # Gap 8: 191-194 (Final precipice before flagpole)
    chasms = set()
    for g in [
        range(18, 24),
        range(34, 38),
        range(48, 69),
        range(86, 91),
        range(104, 108),
        range(125, 130),
        range(157, 165),
        range(191, 195)
    ]:
        chasms.update(g)

    for c in range(cols):
        if c not in chasms:
            grid[13][c] = 1
            grid[14][c] = 1

    def place_pipe(start_col: int, height_in_tiles: int):
        top_row = 13 - height_in_tiles
        grid[top_row][start_col] = 6
        grid[top_row][start_col + 1] = 7
        for r in range(top_row + 1, 13):
            grid[r][start_col] = 8
            grid[r][start_col + 1] = 9

    # --- ZONE 1: Runway & First Chasm (cols 0-28) ---
    # Single-tile stepping stone in Gap 1
    grid[11][20] = 16  # Indestructible stone pillar at col 20, row 11
    # Brick ceiling above the chasm forcing Mario to jump with precision
    grid[6][19] = 2
    grid[6][20] = 2
    grid[6][21] = 2

    # Single mystery block with coin at col 12
    grid[9][12] = 3

    # --- ZONE 2: High Pipes & Shell Bounce Corridor (cols 29-47) ---
    place_pipe(31, 3)  # Pipe 1 (height 3)
    # Gap 2 is cols 34-37
    # Single floating step at col 35, row 10
    grid[10][35] = 16
    place_pipe(38, 4)  # Pipe 2 (height 4: rows 9-12)
    place_pipe(45, 4)  # Pipe 3 (height 4)

    # Overhead low ceiling bricks between pipes
    for c in range(39, 45):
        grid[5][c] = 2

    # --- ZONE 3: THE GREAT CHASM (cols 48-68) ---
    # 20 tiles of empty void! Floating stepping blocks:
    grid[11][51] = 16  # Step 1
    grid[9][54] = 16   # Step 2
    grid[7][57] = 4    # High Mystery Block with Super Mushroom! (Daredevil reward)
    grid[9][60] = 16   # Step 3
    grid[11][63] = 16  # Step 4
    # 2-tile floating platform with enemy at cols 66-67
    grid[11][66] = 16
    grid[11][67] = 16

    # --- ZONE 4: The Low-Ceiling Goomba Gauntlet (cols 72-92) ---
    # Solid brick roof at row 8 (Mario has only 4 tiles of standing clearance!)
    for c in range(74, 91):
        grid[8][c] = 2

    # Gap 4 is cols 86-90 (right under the low ceiling exit!)
    # Stepping stone at col 88, row 11
    grid[11][88] = 16

    # --- ZONE 5: The Pipe Maze & Shell Trap (cols 94-124) ---
    place_pipe(95, 4)   # Tall pipe
    place_pipe(101, 3)  # Mid pipe
    # Gap 5 is cols 104-107
    grid[10][105] = 16  # Step in gap
    place_pipe(109, 4)  # Tall pipe
    place_pipe(116, 4)  # Tall pipe
    place_pipe(122, 3)  # Pipe

    # Overhead brick traps
    grid[5][98] = 2
    grid[5][100] = 3  # Coin
    grid[5][102] = 2

    # Gap 6 is cols 125-129
    grid[11][127] = 16  # Step in gap

    # --- ZONE 6: The Staircase of Doom (cols 130-167) ---
    # Isolated ascending stepping pillars with 1-tile gaps between them!
    grid[12][131] = 16
    grid[10][133] = 16
    grid[8][135] = 16
    grid[6][137] = 16
    grid[4][139] = 16

    # High suspended fortress runway (rows 4 & 5)
    for c in range(141, 149):
        grid[4][c] = 13  # Castle stone
    grid[4][144] = 4    # Second Super Mushroom

    # Descending steps of doom
    grid[6][151] = 16
    grid[8][153] = 16
    grid[10][155] = 16

    # Gap 7 is cols 157-164! (Huge 8-tile chasm)
    grid[10][159] = 16  # Stepping stone 1
    grid[10][162] = 16  # Stepping stone 2

    place_pipe(166, 3)  # Recovery pipe

    # --- ZONE 7: Final Pyramid & Flagpole Precipice (cols 169-208) ---
    # Staircase ascending cols 175-182 (8 steps high)
    for step in range(8):
        c = 175 + step
        for r in range(12 - step, 13):
            grid[r][c] = 16

    # High drop at col 183
    for r in range(5, 13):
        grid[r][183] = 16

    # Gap 8: cols 191-194 right before the flagpole!
    # Single stepping stone in the pit at col 193
    grid[11][193] = 16

    # Flagpole base at col 198
    grid[12][198] = 12
    for r in range(3, 12):
        grid[r][198] = 11
    grid[2][198] = 10

    # Castle: cols 202 to 208
    for r in range(8, 13):
        for c in range(202, 208):
            grid[r][c] = 13
    grid[11][204] = 14
    grid[12][204] = 14
    for c in range(202, 208, 2):
        grid[7][c] = 15

    # 26 Aggressive Enemy Spawns (Goomba Battalions & Koopa Shell Trappers)
    enemies = [
        # Runway Goomba pair
        {"type": "goomba", "x": 14 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 16 * 16, "y": 12 * 16},

        # Chasm landing guard
        {"type": "goomba", "x": 26 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 28 * 16, "y": 12 * 16},

        # Pipe corridor Koopa (dangerous ricochet!)
        {"type": "koopa", "x": 33 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 42 * 16, "y": 12 * 16},

        # Great Chasm 2-tile platform Goomba
        {"type": "goomba", "x": 66 * 16, "y": 10 * 16},

        # Low-Ceiling Gauntlet Battalion (4 Goombas marching tightly!)
        {"type": "goomba", "x": 76 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 78 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 81 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 83 * 16, "y": 12 * 16},

        # Pipe Maze Enemies
        {"type": "goomba", "x": 98 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 100 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 112 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 119 * 16, "y": 12 * 16},

        # Fortress Top Patrol
        {"type": "goomba", "x": 143 * 16, "y": 3 * 16},
        {"type": "goomba", "x": 146 * 16, "y": 3 * 16},

        # Pre-Staircase Assault Squad
        {"type": "goomba", "x": 169 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 171 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 173 * 16, "y": 12 * 16},

        # Final Flagpole Guard
        {"type": "goomba", "x": 188 * 16, "y": 12 * 16},
        {"type": "goomba", "x": 190 * 16, "y": 12 * 16},
        {"type": "koopa", "x": 196 * 16, "y": 12 * 16},
    ]

    # Challenging floating coins
    coins = [
        {"x": 20 * 16 + 8, "y": 9 * 16},
        {"x": 35 * 16 + 8, "y": 8 * 16},
        {"x": 51 * 16 + 8, "y": 9 * 16},
        {"x": 54 * 16 + 8, "y": 7 * 16},
        {"x": 60 * 16 + 8, "y": 7 * 16},
        {"x": 63 * 16 + 8, "y": 9 * 16},
        {"x": 105 * 16 + 8, "y": 8 * 16},
        {"x": 144 * 16 + 8, "y": 2 * 16},
        {"x": 159 * 16 + 8, "y": 8 * 16},
        {"x": 162 * 16 + 8, "y": 8 * 16},
        {"x": 193 * 16 + 8, "y": 9 * 16},
    ]

    return {
        "world": "8-4 (KAİZO EXTREME)",
        "difficulty": "extreme",
        "time": 200,  # Fast high-stress timer!
        "rows": rows,
        "cols": cols,
        "tile_size": 16,
        "pixel_width": cols * 16,
        "pixel_height": rows * 16,
        "grid": grid,
        "coins": coins,
        "enemies": enemies,
        "scenery": [
            {"type": "cloud", "x": 10 * 16, "y": 2 * 16},
            {"type": "hill", "x": 4 * 16, "y": 11 * 16},
            {"type": "cloud", "x": 60 * 16, "y": 2 * 16},
            {"type": "cloud", "x": 120 * 16, "y": 2 * 16},
            {"type": "hill", "x": 170 * 16, "y": 11 * 16},
        ],
        "spawn": {"x": 3 * 16, "y": 12 * 16},
        "flagpole": {"col": 198, "top_row": 2, "base_row": 12},
        "castle": {"x": 202 * 16, "door_x": 204 * 16 + 8},
    }


def get_world_1_1(difficulty: str = "extreme") -> Dict[str, Any]:
    """
    Main entry point for level generation.
    Supports 'extreme' (default) and 'normal'.
    """
    if difficulty.lower() == "normal":
        return get_classic_level()
    return get_extreme_level()
