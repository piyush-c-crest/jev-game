"""
main.py - Entry point for Jev Plays the Game.
Starts the autonomous dungeon crawler powered by TypeSafe AI's Jev model.
"""

from __future__ import annotations
import argparse
import random
import sys

# Ensure UTF-8 console output on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from pathlib import Path

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.rpg import run_game


def main():
    parser = argparse.ArgumentParser(
        description="🎮 Jev Plays the Game — Autonomous Dungeon RPG powered by TypeSafe AI's Jev model."
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.2,
        help="Turn delay in seconds (default: 1.2s; set to 0.1 for fast-forward).",
    )
    parser.add_argument(
        "--floors", "-f",
        type=int,
        default=5,
        help="Total number of dungeon floors to generate (default: 5).",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Optional random seed for reproducible dungeon generation.",
    )

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        run_game(step_delay=args.delay, total_floors=args.floors)
    except KeyboardInterrupt:
        print("\n\nGame paused by user. Farewell, adventurer!")
        sys.exit(0)


if __name__ == "__main__":
    main()
