"""
utils/fs.py - Path constants and JSON I/O helpers.
"""

import sys
import json
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    DEVREF_DIR = Path(sys.executable).parent
else:
    DEVREF_DIR = Path(__file__).resolve().parent.parent

SRC_DIR     = DEVREF_DIR / "src"
REF_DIR     = DEVREF_DIR / "ref"
HEADER_FILE = SRC_DIR / "header.json"
NOTES_DIR   = DEVREF_DIR / "notes"

SRC_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)

# ─── JSON helpers ─────────────────────────────────────────────────────────────
def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
