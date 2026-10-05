from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).with_name("backend")
sys.path.insert(0, str(BACKEND_DIR))

from backend.app import app

__all__ = ["app"]
