"""
commands/cmd_import.py - --import command (import a tool from a JSON file).
"""

from pathlib import Path

from components.display import warn, success
from utils.fs import load_json
from utils.header import (load_header, save_header, load_tool_ref,
                          save_tool_ref, find_tool_keys)
from utils.ids import generate_hex_id, normalise


def cmd_import(raw_args: list):
    """
    devref --import <file>                           → add the file as a new tool
    devref --import <file> --tool <name> --topic     → add the file as a topic to the existing tool name
    """
    if not raw_args:
        warn("Usage: devref --import <file>  [--tool <name>]  [--topic]")
        return

    src_path = Path(raw_args[0])
    if not src_path.exists():
        warn(f"File not found: {src_path}")
        return

    # Parse --tool <name>
    tool_name = None
    if "--tool" in raw_args:
        idx        = raw_args.index("--tool")
        tool_parts = []
        for a in raw_args[idx + 1:]:
            if a.startswith("--"):
                break
            tool_parts.append(a)
        tool_name = normalise(" ".join(tool_parts)) if tool_parts else None

    # --topic flag (no file argument, just a flag)
    topic = 1 if "--topic" in raw_args else 0

    try:
        new_data = load_json(src_path)
    except Exception as e:
        warn(f"Could not parse JSON: {e}")
        return

    if not isinstance(new_data, dict) or not new_data:
        warn("Empty or invalid JSON.")
        return

    header_data = load_header()

    if tool_name and topic == 1:
        # Import src_path as topics into existing tool named tool_name
        try:
            topic_data = load_json(src_path)
        except Exception as e:
            warn(f"Could not parse topic file: {e}")
            return
        _import_topics_into_tool(header_data, tool_name, topic_data)
        return

    if tool_name:
        _import_as_new_tool(header_data, tool_name, new_data)
        return

    # Auto-detect: exported tool file (has "topics" key at root)
    if "topics" in new_data:
        inferred_name = tool_name or normalise(new_data.get("name", src_path.stem))
        _import_as_new_tool(header_data, inferred_name, new_data)
        return

    warn("Could not determine import type. Use --tool <name> to specify.")


def _import_as_new_tool(header_data: dict, tool_key: str, data: dict):
    existing = find_tool_keys(tool_key, header_data)
    if existing:
        # Merge topics into existing tool
        real_key = existing[0]
        ref_data = load_tool_ref(real_key)
        count    = 0
        for tname, tdata in data.get("topics", {}).items():
            norm = normalise(tname)
            ref_data.setdefault("topics", {})[norm] = tdata
            if norm not in header_data[real_key].get("topics", []):
                header_data[real_key].setdefault("topics", []).append(norm)
            count += 1
        save_tool_ref(real_key, ref_data)
        save_header(header_data)
        success(f"Merged {count} topics into existing '{real_key}'.")
        return

    desc      = data.get("description", "")
    tags      = data.get("tags", [])
    tool_type = data.get("type", "")
    topics    = data.get("topics", {})
    hex_id    = data.get("id") or generate_hex_id()

    header_data.setdefault("tools", []).append(tool_key)
    topic_list = [topic for topic in topics.keys()]
    entry = {
        "id":          hex_id,
        "name":        data.get("name", tool_key),
        "tags":        tags,
        "description": desc,
        # "topics":      list(topics.keys())
        # "topics": [x.lower() for x in topic_list]
        "topics" : [normalise(x) for x in topic_list]
    }
    if tool_type:
        entry["type"] = tool_type
    header_data[tool_key] = entry

    for each_topic in topic_list:
        topics[normalise(each_topic)] = topics.pop(each_topic)

    ref_data = {"id": hex_id, "name": tool_key, "topics": topics}
    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"'{tool_key}' imported with {len(topics)} topics.")


def _import_topics_into_tool(header_data: dict, tool_key: str, topic_data: dict):
    """Add topics from topic_data dict into an existing tool."""
    matches = find_tool_keys(tool_key, header_data)
    if not matches:
        warn(f"Tool '{tool_key}' not found after creation — this shouldn't happen.")
        return
    real_key = matches[0]
    ref_data = load_tool_ref(real_key)
    count    = 0

    # topic_data may be {topic_name: {...}} directly, or {"topics": {topic_name: {...}}}
    topics_dict = topic_data.get("topics", topic_data)
    for tname, tdata in topics_dict.items():
        if tname in ("id", "name", "description", "tags", "type"):
            continue
        norm = normalise(tname)
        ref_data.setdefault("topics", {})[norm] = tdata
        if norm not in header_data[real_key].get("topics", []):
            header_data[real_key].setdefault("topics", []).append(norm)
        count += 1

    save_tool_ref(real_key, ref_data)
    save_header(header_data)
    success(f"Added {count} topic(s) to '{real_key}'.")
