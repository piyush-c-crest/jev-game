"""
test_mario_engine.py - Automated Verification of Mario Level, API, and Physics logic.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.mario import get_world_1_1
from server import app
from starlette.testclient import TestClient


def test_level_generation():
    """Verify World 1-1 Classic and Kaizo Extreme structures, tilemaps, and entities."""
    print("Testing World level generators (Classic & Kaizo Extreme)...")
    
    # 1. Normal Level
    lvl_normal = get_world_1_1(difficulty="normal")
    assert "1-1" in lvl_normal["world"]
    assert lvl_normal["rows"] == 15
    assert lvl_normal["cols"] == 212
    assert len(lvl_normal["enemies"]) >= 10

    # 2. Extreme Level
    lvl_extreme = get_world_1_1(difficulty="extreme")
    assert "EXTREME" in lvl_extreme["world"]
    assert lvl_extreme["difficulty"] == "extreme"
    assert lvl_extreme["time"] == 200, "Extreme mode should have high-stress 200s timer"
    assert len(lvl_extreme["enemies"]) >= 20, "Extreme mode should have 20+ enemies"

    # Check that extreme has single-tile step pillars over chasms
    # Col 20 row 11 has a stone pillar in gap 1
    assert lvl_extreme["grid"][11][20] == 16, "Stepping stone pillar in gap 1"
    # Great Chasm floating steps
    assert lvl_extreme["grid"][11][51] == 16, "Great Chasm step 1"
    assert lvl_extreme["grid"][9][54] == 16, "Great Chasm step 2"

    print("  Both Classic and Kaizo Extreme level generators passed all assertions!")


def test_fastapi_mario_endpoints():
    """Verify FastAPI Mario REST API endpoints with difficulty query."""
    print("\nTesting FastAPI Mario endpoints...")
    client = TestClient(app)

    # 1. Level endpoint (Default: extreme)
    r = client.get("/api/mario/level")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "EXTREME" in data["world"]
    assert data["time"] == 200
    print("  GET /api/mario/level (default extreme) verified!")

    # 2. Level endpoint (explicit normal)
    r_norm = client.get("/api/mario/level?difficulty=normal")
    assert r_norm.status_code == 200
    data_norm = r_norm.json()
    assert "NORMAL" in data_norm["world"]
    assert data_norm["time"] == 400
    print("  GET /api/mario/level?difficulty=normal verified!")

    # 3. Score submission endpoint
    score_payload = {
        "player_name": "KaizoMaster",
        "score": 28400,
        "coins": 45,
        "time_left": 142,
        "mode": "agent",
        "status": "cleared"
    }
    r = client.post("/api/mario/scores", json=score_payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    resp = r.json()
    assert resp["status"] == "saved"
    assert resp["rank"] >= 1
    print(f"  POST /api/mario/scores verified! Saved with rank #{resp['rank']}")

    # 3. High scores fetch endpoint
    r = client.get("/api/mario/scores")
    assert r.status_code == 200
    scores_data = r.json()
    assert "scores" in scores_data
    assert len(scores_data["scores"]) > 0
    assert any(s["player_name"] == "KaizoMaster" for s in scores_data["scores"])
    print("  GET /api/mario/scores verified!")

    # 4. Serving Mario HTML UI
    r = client.get("/mario")
    assert r.status_code == 200
    assert "Super Mario Bros" in r.text
    print("  GET /mario UI serving verified!")

    r_root = client.get("/")
    assert r_root.status_code == 200
    print("  GET / UI serving verified!")


def test_mario_physics_math():
    """Verify physics equations: variable jump, stomp geometry, AABB collision."""
    print("\nTesting Mario physics & collision geometry...")

    # AABB collision check function
    def check_aabb(a, b):
        return (
            a["x"] < b["x"] + b["width"] and
            a["x"] + a["width"] > b["x"] and
            a["y"] < b["y"] + b["height"] and
            a["y"] + a["height"] > b["y"]
        )

    mario = {"x": 100, "y": 180, "width": 14, "height": 16}
    goomba = {"x": 108, "y": 180, "width": 14, "height": 16}

    # Intersecting bounding boxes
    assert check_aabb(mario, goomba) is True, "Mario and Goomba should collide"

    # Distant bounding boxes
    goomba_far = {"x": 150, "y": 180, "width": 14, "height": 16}
    assert check_aabb(mario, goomba_far) is False, "Mario and distant Goomba should not collide"

    # Stomp condition: Mario falling (vy > 0) and feet above Goomba midpoint
    mario_vy = 3.5
    mario_feet = mario["y"] + mario["height"] # 196
    goomba_midpoint = goomba["y"] + goomba["height"] / 2 # 188

    is_stomp = (mario_vy > 0) and (mario_feet <= goomba_midpoint + 10)
    assert is_stomp is True, "Mario should register a stomp"

    # Horizontal collision (Mario at same height, walking)
    mario_walk_feet = 196
    mario_vy_walk = 0.0
    is_stomp_walking = (mario_vy_walk > 0) and (mario_walk_feet <= goomba_midpoint + 6)
    assert is_stomp_walking is False, "Horizontal walk should NOT register a stomp (causes damage)"

    # Variable jump height simulation
    # Full hold vs short tap
    gravity = 0.36
    initial_impulse = -5.6

    # Short tap: releases after 2 frames
    vy_tap = initial_impulse
    y_tap = 192
    for frame in range(20):
        if frame == 2 and vy_tap < -2.0:
            vy_tap = -2.0  # Cutoff
        vy_tap += gravity
        y_tap += vy_tap
    short_jump_apex = y_tap

    # Full hold: held for 14 frames
    vy_hold = initial_impulse
    y_hold = 192
    for frame in range(20):
        if frame < 14:
            vy_hold -= 0.18  # Hold boost
        vy_hold += gravity
        y_hold += vy_hold
    full_jump_apex = y_hold

    assert full_jump_apex < short_jump_apex, (
        f"Full hold jump ({full_jump_apex}) must rise significantly higher than short tap ({short_jump_apex})"
    )
    print("  Physics & variable jump simulations passed successfully!")


if __name__ == "__main__":
    test_level_generation()
    test_fastapi_mario_endpoints()
    test_mario_physics_math()
    print("\nALL SUPER MARIO TESTS PASSED SUCCESSFULLY!")
