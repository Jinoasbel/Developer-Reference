"""
components/editor.py - Console editor helpers (vim/nano/notepad).
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

from components.display import warn


def open_console_editor(initial_content: str) -> str:
    """
    Open a temp file in the user's preferred console editor (vim/nano/notepad).
    Returns the saved content.
    """
    editors = []
    env_editor = os.environ.get("EDITOR", "")
    if env_editor:
        editors.append(env_editor)

    if sys.platform == "win32":
        editors += ["notepad.exe"]
    else:
        editors += ["nano", "vim", "vi"]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     encoding="utf-8", delete=False) as f:
        f.write(initial_content)
        tmp_path = f.name

    editor_used = None
    for ed in editors:
        try:
            subprocess.call([ed, tmp_path])
            editor_used = ed
            break
        except (FileNotFoundError, OSError):
            continue

    if not editor_used:
        warn("No console editor found. Set $EDITOR environment variable.")
        Path(tmp_path).unlink(missing_ok=True)
        return initial_content

    with open(tmp_path, "r", encoding="utf-8") as f:
        result = f.read()
    Path(tmp_path).unlink(missing_ok=True)
    return result


def open_console_editor_json(initial_dict: dict) -> dict | None:
    """Open a dict as JSON in the console editor; returns parsed result or None on error."""
    content = json.dumps(initial_dict, indent=2, ensure_ascii=False)
    edited  = open_console_editor(content)
    try:
        return json.loads(edited)
    except json.JSONDecodeError as e:
        warn(f"Invalid JSON after editing: {e}")
        return None
