"""
commands/cmd_del.py - --del command (delete a tool or topic).
"""

from components.display import c, warn, success
from utils.header import (load_header, save_header, load_tool_ref,
                          save_tool_ref, tool_ref_path, find_tool_keys, resolve_tool)
from utils.ids import normalise


def cmd_del(raw_args: list):
    if not raw_args:
        warn("Usage: devref --del <tool>  OR  devref --del <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args)
    header_data      = load_header()
    matches          = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"Tool '{tool_query}' not found.")
        return
    tool_key = matches[0]

    if "--topic" in rest:
        idx         = rest.index("--topic")
        topic_parts = []
        for a in rest[idx + 1:]:
            if a.startswith("--"):
                break
            topic_parts.append(a)
        topic_name = normalise(" ".join(topic_parts))
        if not topic_name:
            warn("Provide a topic name.")
            return
        ref_data = load_tool_ref(tool_key)
        if topic_name not in ref_data.get("topics", {}):
            warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
            return
        confirm = input(c(f"\n  Type '{topic_name}' to confirm deletion: ", "yellow")).strip()
        if normalise(confirm) != normalise(topic_name):
            warn("Cancelled.")
            return
        del ref_data["topics"][topic_name]
        save_tool_ref(tool_key, ref_data)
        if topic_name in header_data[tool_key].get("topics", []):
            header_data[tool_key]["topics"].remove(topic_name)
        save_header(header_data)
        success(f"Topic '{topic_name}' deleted from '{tool_key}'.")
        return

    # Delete entire tool
    confirm = input(c(f"\n  Type '{tool_key}' to confirm deleting ALL of '{tool_key}': ", "yellow")).strip()
    if normalise(confirm) != normalise(tool_key):
        warn("Cancelled.")
        return
    if tool_key in header_data.get("tools", []):
        header_data["tools"].remove(tool_key)
    if tool_key in header_data:
        del header_data[tool_key]
    save_header(header_data)
    ref_path = tool_ref_path(tool_key)
    if ref_path.exists():
        ref_path.unlink()
    success(f"'{tool_key}' deleted.")
