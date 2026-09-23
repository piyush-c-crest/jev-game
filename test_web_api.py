"""
test_web_api.py - Comprehensive verification of GameSession and FastAPI endpoints.
"""

import sys
import os

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.abspath("."))

from game_session import GameSession
from server import app
from starlette.testclient import TestClient


def test_game_session():
    print("Testing GameSession unit logic...")
    session = GameSession(floors=3, mode="manual", seed=42)
    state = session.get_state()

    assert state["status"] == "PLAYING", f"Expected PLAYING, got {state['status']}"
    assert state["player"]["health"] == 100, f"Expected 100 HP, got {state['player']['health']}"
    assert state["dungeon"]["total_floors"] == 3
    assert len(state["available_actions"]) > 0, "Expected available actions"
    print("  Initial state verified:", state["encounter_phase"], "actions:", state["available_actions"])

    # Test Player Action
    action = state["available_actions"][0]
    print(f"  Executing player action: {action}")
    new_state = session.execute_player_action(action)
    assert new_state["player"]["total_turns"] == 1, "Turn count should be 1"
    assert new_state["last_outcome"] is not None, "last_outcome should be populated"
    print("  Turn outcome:", new_state["last_outcome"]["summary"])

    # Test Agent Step
    print("  Executing agent step...")
    agent_state = session.execute_agent_turn()
    assert agent_state["player"]["total_turns"] == 2, "Turn count should be 2"
    assert agent_state["last_decision"] is not None, "Agent should produce last_decision"
    print("  Agent decision:", agent_state["last_decision"]["action"], "confidence:", agent_state["last_decision"]["confidence"])

    # Test Advisor Query
    print("  Querying advisor...")
    advice = session.get_agent_advice()
    assert "action" in advice, f"Expected action in advice, got {advice}"
    assert "confidence" in advice
    print("  Advisor recommended:", advice["action"], "probabilities:", advice.get("probabilities"))

    print("GameSession unit tests passed successfully!")


def test_fastapi_endpoints():
    print("\nTesting FastAPI HTTP endpoints with TestClient...")
    client = TestClient(app)

    # Health
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    health = r.json()
    assert health["status"] == "ok"
    print("  /api/health -> OK (API Key configured:", health["api_key_configured"], ")")

    # New game
    r = client.post("/api/game/new", json={"floors": 4, "mode": "manual", "seed": 100})
    assert r.status_code == 200
    state = r.json()
    assert state["dungeon"]["total_floors"] == 4
    print("  POST /api/game/new -> OK")

    # Get state
    r = client.get("/api/game/state")
    assert r.status_code == 200
    state = r.json()
    assert state["status"] == "PLAYING"
    print("  GET /api/game/state -> OK")

    # Mode switch
    r = client.post("/api/game/mode", json={"mode": "agent"})
    assert r.status_code == 200
    assert r.json()["mode"] == "agent"
    print("  POST /api/game/mode -> OK")

    # Action
    r = client.post("/api/game/action", json={"action": state["available_actions"][0]})
    assert r.status_code == 200
    action_res = r.json()
    assert action_res["last_outcome"] is not None
    print("  POST /api/game/action -> OK")

    # Agent Step
    r = client.post("/api/game/agent-step")
    assert r.status_code == 200
    step_res = r.json()
    assert step_res["last_decision"] is not None
    print("  POST /api/game/agent-step -> OK")

    # Advisor
    r = client.get("/api/game/advisor")
    assert r.status_code == 200
    advice = r.json()
    assert "action" in advice
    print("  GET /api/game/advisor -> OK")

    # Index HTML
    r = client.get("/")
    assert r.status_code == 200
    assert "Jev Plays the Game" in r.text
    print("  GET / -> OK (HTML served)")

    # Static CSS
    r = client.get("/static/css/game.css")
    assert r.status_code == 200
    assert "app-container" in r.text
    print("  GET /static/css/game.css -> OK")

    # Static JS
    r = client.get("/static/js/game.js")
    assert r.status_code == 200
    assert "WebGameApp" in r.text
    print("  GET /static/js/game.js -> OK")

    r = client.get("/static/js/audio.js")
    assert r.status_code == 200
    assert "SoundFX" in r.text
    print("  GET /static/js/audio.js -> OK")

    print("\nAll FastAPI API endpoints passed successfully!")


if __name__ == "__main__":
    test_game_session()
    test_fastapi_endpoints()
    print("\n[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY!")
