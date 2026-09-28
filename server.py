"""
server.py - FastAPI Web Server for Jev Plays the Game.
Serves REST API endpoints and static assets for the browser Web RPG interface.
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
from typing import Optional, Any
import webbrowser

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time

# Load environment variables (.env)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.rpg import GameSession
from src.mario import get_world_1_1
from src.chess import ChessSession, ChessAgentProfile

WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(
    title="🍄 Super Mario Bros Web Platformer & Jev Plays the Game",
    description="Browser platformer with autonomous AI agent & Jev RPG dual-play.",
    version="1.2.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active game session instance
active_session: GameSession = GameSession(floors=5, mode="manual")

# In-memory Mario leaderboard
mario_scores: list[dict] = [
    {"player_name": "MarioBot-Pro", "score": 12850, "coins": 24, "time_left": 286, "mode": "agent", "status": "cleared", "timestamp": int(time.time()) - 3600},
    {"player_name": "Player 1", "score": 9400, "coins": 18, "time_left": 210, "mode": "manual", "status": "cleared", "timestamp": int(time.time()) - 7200},
    {"player_name": "Luigi", "score": 5200, "coins": 11, "time_left": 150, "mode": "manual", "status": "game_over", "timestamp": int(time.time()) - 10800},
]


# Request schemas
class NewGameRequest(BaseModel):
    floors: int = 5
    mode: str = "manual"
    seed: Optional[int] = None


class ActionRequest(BaseModel):
    action: str


class ModeRequest(BaseModel):
    mode: str


class MarioScoreRequest(BaseModel):
    player_name: str = "Mario"
    score: int
    coins: int = 0
    time_left: int = 0
    mode: str = "manual"  # "manual" or "agent"
    status: str = "cleared"  # "cleared" or "game_over"


# Active Chess session instance
active_chess_session: ChessSession = ChessSession()


class ChessNewGameRequest(BaseModel):
    starting_fen: Optional[str] = None
    white_persona: Optional[str] = None
    black_persona: Optional[str] = None


class ChessStepRequest(BaseModel):
    fen: Optional[str] = None
    legal_moves: Optional[list[Any]] = None
    in_check: bool = False
    history: Optional[list[str]] = None
    is_game_over: bool = False
    game_over_reason: Optional[str] = None


ChessNewGameRequest.model_rebuild()
ChessStepRequest.model_rebuild()


# REST Endpoints - Mario Platformer
@app.get("/api/mario/level")
def get_mario_level(difficulty: str = "extreme"):
    """Return the tilemap configuration and entity placements for World 1-1 (Normal or Extreme)."""
    return get_world_1_1(difficulty=difficulty)


@app.post("/api/mario/scores")
def submit_mario_score(req: MarioScoreRequest):
    """Save a completed or game-over run score."""
    entry = req.model_dump()
    entry["timestamp"] = int(time.time())
    mario_scores.append(entry)
    mario_scores.sort(key=lambda x: x["score"], reverse=True)
    return {
        "status": "saved",
        "rank": mario_scores.index(entry) + 1,
        "top_scores": mario_scores[:10],
    }


@app.get("/api/mario/scores")
def get_mario_scores():
    """Retrieve top Mario scores."""
    return {"scores": mario_scores[:20]}


# REST Endpoints - Jev RPG
@app.post("/api/game/new")
def new_game(req: NewGameRequest):
    """Start a fresh dungeon crawl session."""
    global active_session
    active_session = GameSession(floors=req.floors, mode=req.mode, seed=req.seed)
    return active_session.get_state()


@app.get("/api/game/state")
def get_state():
    """Fetch current game state, available actions, and turn log."""
    return active_session.get_state()


@app.post("/api/game/action")
def execute_action(req: ActionRequest):
    """Execute a manual player action (Attack, Defend, Potion, Flee, Explore, Fork)."""
    return active_session.execute_player_action(req.action)


@app.post("/api/game/agent-step")
def agent_step():
    """Trigger one autonomous turn by Jev System One."""
    return active_session.execute_agent_turn()


@app.get("/api/game/advisor")
def get_advisor():
    """Query Jev System One for tactical advice without committing a turn."""
    return active_session.get_agent_advice()


@app.post("/api/game/mode")
def set_mode(req: ModeRequest):
    """Switch seamlessly between 'manual' and 'agent' mode."""
    if req.mode not in ("manual", "agent"):
        raise HTTPException(status_code=400, detail="Mode must be 'manual' or 'agent'")
    active_session.mode = req.mode
    return {"mode": active_session.mode}


@app.get("/api/health")
def health_check():
    """Verify backend health and TypeSafe API configuration."""
    api_key = os.getenv("TYPESAFE_API_KEY")
    return {
        "status": "ok",
        "api_key_configured": bool(api_key),
        "api_key_preview": f"{api_key[:6]}..." if api_key else None,
        "mode": active_session.mode,
        "game_status": active_session.status,
    }


# REST Endpoints - Jev vs Jev Chess
@app.post("/api/chess/new")
def new_chess_game(req: ChessNewGameRequest):
    """Start or initialize a new JEV vs JEV Chess match."""
    global active_chess_session
    active_chess_session = ChessSession(starting_fen=req.starting_fen or "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    return active_chess_session.get_state()


@app.get("/api/chess/state")
def get_chess_state():
    """Fetch current Chess match state, dual agent decisions, and move log."""
    return active_chess_session.get_state()


@app.post("/api/chess/step")
def step_chess_game(req: ChessStepRequest):
    """Trigger the current active JEV agent (White or Black) to analyze and make a move."""
    return active_chess_session.execute_agent_step(
        fen=req.fen,
        legal_moves=req.legal_moves,
        in_check=req.in_check,
        client_history=req.history,
        is_game_over=req.is_game_over,
        game_over_reason=req.game_over_reason,
    )


@app.post("/api/chess/reset")
def reset_chess_game():
    """Reset the Chess board and match session to the starting position."""
    active_chess_session.reset()
    return active_chess_session.get_state()


# Static assets & HTML serving
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
@app.get("/mario")
def mario_index():
    """Serve the Super Mario Arcade Platformer UI."""
    mario_file = WEB_DIR / "mario.html"
    if mario_file.exists():
        return FileResponse(str(mario_file))
    index_file = WEB_DIR / "index.html"
    return FileResponse(str(index_file))


@app.get("/rpg")
def rpg_index():
    """Serve the original Jev RPG UI."""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return {"error": "web/index.html not found."}
    return FileResponse(str(index_file))


@app.get("/chess")
def chess_index():
    """Serve the JEV vs JEV Chess Arena UI."""
    chess_file = WEB_DIR / "chess.html"
    if not chess_file.exists():
        return {"error": "web/chess.html not found."}
    return FileResponse(str(chess_file))


def main():
    default_port = int(os.environ.get("PORT", 8000))
    default_host = os.environ.get("HOST", "0.0.0.0")
    parser = argparse.ArgumentParser(description="Start Jev Plays the Game Web Server.")
    parser.add_argument("--port", "-p", type=int, default=default_port, help=f"Server port (default: {default_port})")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host address (default: {default_host})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    import uvicorn

    url = f"http://{args.host}:{args.port}"
    print(f"🎮 Starting Jev Plays the Game Web Server at {url}")

    # Only attempt to open browser if not in a cloud environment (e.g. Railway)
    is_cloud = "RAILWAY_ENVIRONMENT" in os.environ or "PORT" in os.environ
    if not args.no_browser and not is_cloud:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
