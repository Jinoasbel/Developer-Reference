"""
commands/cmd_edit.py - --edit command (edit tool or topic).
"""

from components.display import warn, success
from components.editor import open_console_editor_json
from utils.header import (load_header, save_header, load_tool_ref,
                          save_tool_ref, find_tool_keys, resolve_tool)
from utils.ids import normalise


def cmd_edit(raw_args: list):
    if not raw_args:
        warn("Usage: devref --edit <tool>  OR  devref --edit <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args, normal_flag=False)
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
            topic_parts.append(a) # append <topic> to topic_parts []
        topic_name = normalise(" ".join(topic_parts))
        if not topic_name:
            warn("Provide a topic name.")
            return
        ref_data = load_tool_ref(tool_key)
        topics   = ref_data.get("topics", {}) # remove this line
        if topic_name:
            for def_topic in topics:
                if topic_name == normalise(def_topic):
                    topic_name = def_topic
        else:
            warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
            return
        # --------------------------------------

        """
        what the below block seems to do is..
        when topic name is in topics 
        current <- topic 
        """
        # if topic_name not in topics:
        #     warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
        #     return
        current = topics[topic_name]
        edited  = open_console_editor_json(current)
        if edited is None:
            return
        topics[topic_name]  = edited
        ref_data["topics"]  = topics
        save_tool_ref(tool_key, ref_data)
        success(f"Topic '{topic_name}' updated!")
        return

    # Edit tool-level fields: name, description, tags only
    entry    = header_data[tool_key]
    editable = {
        "name":        entry.get("name", tool_key),
        "description": entry.get("description", ""),
        "tags":        entry.get("tags", []),
    }
    edited = open_console_editor_json(editable)
    if edited is None:
        return
    entry["name"]          = edited.get("name", entry["name"])
    entry["description"]   = edited.get("description", entry["description"])
    entry["tags"]          = edited.get("tags", entry["tags"])
    header_data[tool_key]  = entry
    save_header(header_data)
    success(f"Tool '{tool_key}' updated!")
