"""
commands/cmd_new.py - --new command (create a new tool entry).
"""

import json

from components.display import c, warn, success, tip
from components.editor import open_console_editor
from components.wizard import HINTS, ask, ask_list, collect_topic_data, collect_tool_type
from utils.header import load_header, save_header, save_tool_ref, find_tool_keys, resolve_tool, add_tool_to_header
from utils.ids import generate_hex_id, normalise


def cmd_new(raw_args: list):
    if not raw_args:
        warn("Usage: devref --new <tool>")
        return

    tool_query, rest = resolve_tool(raw_args, normal_flag = False) #returns with how the data is written when false
    use_notepad      = "--notepad" in rest

    if not tool_query:
        warn("Usage: devref --new <tool>")
        return

    header_data = load_header()
    existing    = find_tool_keys(tool_query, header_data)
    if existing:
        warn(f"'{tool_query}' already exists. Use  devref --add {tool_query} --topic <name>  instead.")
        return

    tool_key = tool_query  # normalised name used as key

    if use_notepad:
        template = {
            "id":   generate_hex_id(),
            "name": tool_key,
            "type": "interpreter | cmdlinetool | framework | library | builtin | packagemanager",
            "topics": {
                "exampletopic": {
                    "name":         "exampletopic",
                    "type":         "subcommand | flag | concept | workflow",
                    "tags":         ["tag1"],
                    "description":  "What this topic is about",
                    "what_it_does": "Detailed explanation",
                    "syntax":       ["command --flag <required>"],
                    "examples":     ["command --flag value"],
                    "flags":        {"--verbose": "enable verbose output"},
                    "arguments":    {"<path>": "path to input file"}
                }
            }
        }
        content = json.dumps(template, indent=2, ensure_ascii=False)
        edited  = open_console_editor(content)
        try:
            parsed = json.loads(edited)
        except json.JSONDecodeError as e:
            warn(f"Invalid JSON: {e}")
            return
        _apply_new_tool_from_parsed(tool_key, parsed, header_data)
        return

    # Terminal wizard
    print(c(f"\n  Creating new tool: {tool_key.upper()}", "bright"))
    desc     = ask("Tool description:", hint=HINTS["tool_desc"])
    tool_type= collect_tool_type()
    tags_raw = ask("Tags (comma-separated):", hint=HINTS["tool_tags"])
    tags     = [t.strip() for t in tags_raw.split(",") if t.strip()]

    hex_id   = add_tool_to_header(header_data, tool_key, desc, tags, tool_type=tool_type)
    ref_data = {"id": hex_id, "name": tool_key, "topics": {}}

    print(c("\n  Now add topics. Blank topic name to finish.", "cyan"))
    while True:
        tname_raw = ask("\n  Topic name (blank to finish):", hint=HINTS["topic_name"])
        if not tname_raw:
            break
        # tname = normalise(tname_raw)
        tname = tname_raw
        tdata = collect_topic_data()
        ref_data["topics"][tname] = tdata
        header_data[tool_key]["topics"].append(tname)

    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"'{tool_key}' added!")
    tip(f"Run:  devref --find {tool_key}")


def _apply_new_tool_from_parsed(tool_key: str, parsed: dict, header_data: dict):
    """Save a new tool from a parsed dict (notepad flow)."""
    desc       = parsed.get("description", "")
    tags       = parsed.get("tags", [])
    tool_type  = parsed.get("type", "")
    topics_dict= parsed.get("topics", {})
    topic_keys = list(topics_dict.keys())
    hex_id     = parsed.get("id") or generate_hex_id()

    header_data.setdefault("tools", [])
    if tool_key not in header_data["tools"]:
        header_data["tools"].append(tool_key)
    entry = {
        "id":          hex_id,
        "name":        tool_key,
        "tags":        tags,
        "description": desc,
        "topics":      topic_keys
    }
    if tool_type:
        entry["type"] = tool_type
    header_data[tool_key] = entry
    ref_data = {"id": hex_id, "name": tool_key, "topics": topics_dict}
    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"'{tool_key}' created from editor!")
    tip(f"Run:  devref --find {tool_key}")
