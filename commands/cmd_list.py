"""
commands/cmd_list.py - --list command (list all tools in reference).
"""

from components.display import c, header, warn
from utils.header import load_header


def cmd_list():
    header_data = load_header()
    tools       = header_data.get("tools", [])
    if not tools:
        warn("No entries yet. Run  devref --new <tool>  to start.")
        return
    header("All Tools in Reference")
    for tool_key in sorted(tools):
        entry  = header_data.get(tool_key, {})
        desc   = entry.get("description", "")
        short  = (desc[:48] + "…") if len(desc) > 48 else desc
        tid    = entry.get("id", "??????")
        topics = entry.get("topics", [])
        print(c(f"    [{tid}]", "yellow") + "  " +
              c(entry.get("name", tool_key), "bright") +
              c(f"  [{len(topics)} topics]", "dim"))
        if short:
            print(c(f"        {short}", "dim"))
    print()
