"""
Pytest configuration and environment fixture setup.
Ensures repository root and src directory are on sys.path.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

for path in [ROOT_DIR, SRC_DIR]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
