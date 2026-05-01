"""
commands/cmd_add.py - --add command (add a topic to an existing tool).
"""

import json

from components.display import c, warn, success
from components.editor import open_console_editor
from components.wizard import collect_topic_data
from utils.header import (load_header, save_header, load_tool_ref,
                          save_tool_ref, find_tool_keys, resolve_tool)
from utils.ids import normalise


def cmd_add(raw_args: list, inner_call=0):
    if not raw_args:
        warn("Usage: devref --add <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args)
    use_notepad      = "--notepad" in rest

    header_data = load_header()
    matches     = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"'{tool_query}' not found. Run  devref --new {tool_query}  first.")
        return
    tool_key = matches[0]

    if "--topic" not in rest:
        warn("Usage: devref --add <tool> --topic <name>")
        return

    idx         = rest.index("--topic")
    topic_parts = []
    for a in rest[idx + 1:]:
        if a.startswith("--"):
            break
        topic_parts.append(a)
    topic_name = normalise(" ".join(topic_parts))

    if not topic_name:
        warn("Provide a topic name: devref --add <tool> --topic <name>")
        return

    ref_data = load_tool_ref(tool_key)

    if use_notepad:
        template = {
            topic_name: {
                "name":        topic_name,
                "tags":        [],
                "description": "What this topic is about",
                "what_it_does":"Detailed explanation",
                "syntax":      ["command --flag <required>"],
                "examples":    ["command --flag value"]
            }
        }
        content = json.dumps(template, indent=2, ensure_ascii=False)
        edited  = open_console_editor(content)
        try:
            parsed = json.loads(edited)
        except json.JSONDecodeError as e:
            warn(f"Invalid JSON: {e}")
            return

        for tname, tdata in parsed.items():
            norm = normalise(tname)
            ref_data.setdefault("topics", {})[norm] = tdata
            if norm not in header_data[tool_key].get("topics", []):
                header_data[tool_key].setdefault("topics", []).append(norm)
        save_header(header_data)
        save_tool_ref(tool_key, ref_data)
        success(f"Topic(s) added to '{tool_key}'!")
        return

    print(c(f"\n  Adding topic '{topic_name}' to: {tool_key.upper()}", "bright"))
    tdata = collect_topic_data(inner_call=inner_call)
    ref_data.setdefault("topics", {})[topic_name] = tdata
    header_data[tool_key].setdefault("topics", [])
    if topic_name not in header_data[tool_key]["topics"]:
        header_data[tool_key]["topics"].append(topic_name)
    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"Topic '{topic_name}' added to '{tool_key}'!")
    if inner_call == 1:
        return
