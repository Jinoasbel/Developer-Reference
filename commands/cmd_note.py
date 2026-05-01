"""
commands/cmd_note.py - --note command (manage plain-text notes).
"""

import datetime

from components.display import c, header, warn, success, tip
from components.editor import open_console_editor
from utils.fs import NOTES_DIR
from utils.ids import normalise


def cmd_note(raw_args: list):
    """
    devref --note              → list all notes
    devref --note <name>       → open/create note in console editor
    devref --note <name> --del → delete note
    """
    name_parts = [a for a in raw_args if not a.startswith("--")]
    name       = normalise(" ".join(name_parts)) if name_parts else ""
    do_del     = "--del" in raw_args

    if not name:
        # List all notes
        notes = sorted(NOTES_DIR.glob("*.txt"))
        if not notes:
            tip("No notes yet. Run  devref --note <name>  to create one.")
            return
        header("Notes")
        for n in notes:
            mtime = datetime.datetime.fromtimestamp(n.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(c(f"    {n.stem}", "green") + c(f"  (modified: {mtime})", "dim"))
        print()
        return

    note_path = NOTES_DIR / f"{name}.txt"

    if do_del:
        if not note_path.exists():
            warn(f"Note '{name}' not found.")
            return
        confirm = input(c(f"\n  Type '{name}' to confirm deletion: ", "yellow")).strip()
        if normalise(confirm) != name:
            warn("Cancelled.")
            return
        note_path.unlink()
        success(f"Note '{name}' deleted.")
        return

    # Open or create in console editor
    initial = ""
    if note_path.exists():
        with open(note_path, "r", encoding="utf-8") as f:
            initial = f.read()
    else:
        initial = f"# {name}\n# Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    edited = open_console_editor(initial)

    with open(note_path, "w", encoding="utf-8") as f:
        f.write(edited)

    # Update modification stamp as a footer (non-destructive)
    stamp = f"\n# Last saved: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    with open(note_path, "a", encoding="utf-8") as f:
        f.write(stamp)

    success(f"Note '{name}' saved.")
