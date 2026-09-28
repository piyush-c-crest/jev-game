"""
test_chess_engine.py - Automated Verification of Chess State Builder,
JEV Decision Engine, ChessSession, and FastAPI Endpoints.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chess import (
    parse_fen,
    describe_legal_move,
    heuristic_fallback_move,
    build_chess_context,
    ChessSession,
    STARTING_FEN,
)
from server import app
from starlette.testclient import TestClient


def test_fen_parser():
    print("Testing FEN parser and position info...")
    # Initial board
    info = parse_fen(STARTING_FEN)
    assert info.active_color == "white"
    assert info.fullmove_number == 1
    assert info.white_material == 39
    assert info.black_material == 39
    assert info.material_difference == 0
    assert info.game_phase == "Opening"
    assert len(info.captured_by_white) == 0
    assert len(info.captured_by_black) == 0
    assert "a b c d e f g h" in info.ascii_board

    # Midgame position with White up a Bishop
    fen_mid = "r1bqk2r/pp2bppp/2n1pn2/2pp4/3P4/2PBPN2/PP1N1PPP/R1BQK2R w KQkq - 3 7"
    info_mid = parse_fen(fen_mid)
    assert info_mid.active_color == "white"
    assert info_mid.fullmove_number == 7

    # Endgame position
    fen_end = "8/5pk1/4p1p1/7p/7P/4K1P1/8/8 w - - 0 45"
    info_end = parse_fen(fen_end)
    assert info_end.game_phase == "Endgame"
    print("  FEN parser assertions passed!")


def test_move_descriptions_and_heuristics():
    print("Testing move descriptions and heuristic fallback...")
    # Castling
    desc_castle = describe_legal_move("O-O", "white")
    assert "kingside" in desc_castle.lower()

    # Capture
    move_cap = {"san": "Qxd5", "from": "d1", "to": "d5", "piece": "q", "captured": "p"}
    desc_cap = describe_legal_move(move_cap, "white")
    assert "capture" in desc_cap.lower()
    assert "queen" in desc_cap.lower()

    # Check
    move_chk = {"san": "Bxf7+", "from": "c4", "to": "f7", "piece": "b", "captured": "p"}
    desc_chk = describe_legal_move(move_chk, "white")
    assert "check" in desc_chk.lower()

    # Heuristic fallback move prioritizes captures
    moves = [
        {"san": "a3", "from": "a2", "to": "a3", "piece": "p"},
        {"san": "h3", "from": "h2", "to": "h3", "piece": "p"},
        {"san": "Bxf7+", "from": "c4", "to": "f7", "piece": "b", "captured": "p"},
    ]
    best_move = heuristic_fallback_move(moves, "white")
    assert best_move == "Bxf7+", f"Expected capture/check to be picked, got {best_move}"
    print("  Move descriptions and heuristic fallback passed!")


def test_chess_session_lifecycle():
    print("Testing ChessSession state manager...")
    session = ChessSession()
    state = session.get_state()
    assert state["status"] == "PLAYING"
    assert state["turn"] == "white"
    assert state["move_count"] == 0
    assert state["white_agent"]["name"] == "Jev White (Apollo)"
    assert state["black_agent"]["name"] == "Jev Black (Kronos)"

    # Step White move
    step1 = session.execute_agent_step(
        fen=STARTING_FEN,
        legal_moves=["e4", "d4", "Nf3", "c4"],
        in_check=False,
    )
    assert step1["move_count"] == 1
    assert step1["last_white_decision"] is not None
    assert step1["last_white_decision"]["move"] in ["e4", "d4", "Nf3", "c4"]
    assert step1["turn"] == "black"

    # Step Black move
    fen_after_e4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    step2 = session.execute_agent_step(
        fen=fen_after_e4,
        legal_moves=["e5", "c5", "e6", "d5"],
        in_check=False,
    )
    assert step2["move_count"] == 2
    assert step2["last_black_decision"] is not None
    assert step2["last_black_decision"]["move"] in ["e5", "c5", "e6", "d5"]
    assert step2["turn"] == "white"

    # Reset
    session.reset()
    assert session.move_count == 0
    assert session.turn == "white"
    print("  ChessSession lifecycle assertions passed!")


def test_fastapi_chess_endpoints():
    print("Testing FastAPI Chess endpoints with TestClient...")
    client = TestClient(app)

    # 1. UI Serving
    r_ui = client.get("/chess")
    assert r_ui.status_code == 200
    assert "JEV vs JEV Chess Arena" in r_ui.text
    print("  GET /chess UI served successfully!")

    # 2. State endpoint
    r_state = client.get("/api/chess/state")
    assert r_state.status_code == 200
    state = r_state.json()
    assert state["status"] == "PLAYING"
    assert "white_agent" in state
    assert "black_agent" in state
    print("  GET /api/chess/state verified!")

    # 3. New game endpoint
    r_new = client.post("/api/chess/new", json={"starting_fen": STARTING_FEN})
    assert r_new.status_code == 200
    assert r_new.json()["status"] == "PLAYING"
    print("  POST /api/chess/new verified!")

    # 4. Step endpoint
    r_step = client.post(
        "/api/chess/step",
        json={
            "fen": STARTING_FEN,
            "legal_moves": ["e4", "d4", "Nf3"],
            "in_check": False,
            "history": [],
            "is_game_over": False,
        },
    )
    assert r_step.status_code == 200
    step_data = r_step.json()
    assert step_data["move_count"] >= 1
    assert step_data["last_white_decision"] is not None
    print(f"  POST /api/chess/step verified! Decided move: {step_data['last_white_decision']['move']}")

    # 5. Reset endpoint
    r_reset = client.post("/api/chess/reset")
    assert r_reset.status_code == 200
    assert r_reset.json()["move_count"] == 0
    print("  POST /api/chess/reset verified!")

    # 6. Static files serving
    r_js = client.get("/static/js/chess_app.js")
    assert r_js.status_code == 200
    assert "ChessApp" in r_js.text

    r_audio = client.get("/static/js/chess_audio.js")
    assert r_audio.status_code == 200
    assert "ChessSoundFX" in r_audio.text

    r_pieces = client.get("/static/js/chess_pieces.js")
    assert r_pieces.status_code == 200
    assert "CHESS_PIECES" in r_pieces.text

    r_vendor = client.get("/static/js/vendor/chess.min.js")
    assert r_vendor.status_code == 200

    r_css = client.get("/static/css/chess.css")
    assert r_css.status_code == 200
    assert "chess-arena-layout" in r_css.text

    print("  All static assets and endpoints passed!")


if __name__ == "__main__":
    test_fen_parser()
    test_move_descriptions_and_heuristics()
    test_chess_session_lifecycle()
    test_fastapi_chess_endpoints()
    print("\n[SUCCESS] ALL CHESS TESTS PASSED SUCCESSFULLY!")
