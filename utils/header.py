"""
utils/header.py - Header (master index) and tool-ref file helpers.
"""

from pathlib import Path

from utils.fs import load_json, save_json, HEADER_FILE, REF_DIR
from utils.ids import generate_hex_id, fuzzy_name_match, normalise


# ─── Header helpers ───────────────────────────────────────────────────────────
def load_header() -> dict:
    data = load_json(HEADER_FILE)
    if "tools" not in data:
        data["tools"] = []
    return data

def save_header(data: dict):
    save_json(HEADER_FILE, data)

def get_tool_entry(header_data: dict, tool_key: str) -> dict:
    return header_data.get(tool_key, {})

def find_tool_keys(query: str, header_data: dict) -> list:
    """Return all tool keys in header that match query (case/separator insensitive)."""
    return [key for key in header_data.get("tools", []) if fuzzy_name_match(query, key)]

def add_tool_to_header(header_data: dict, tool_key: str, description: str, tags: list, tool_type: str = "") -> str:
    hex_id = generate_hex_id()
    header_data.setdefault("tools", [])
    if tool_key not in header_data["tools"]:
        header_data["tools"].append(tool_key)
    entry = {
        "id":          hex_id,
        "name":        tool_key,
        "tags":        tags,
        "description": description,
        "topics":      []
    }
    if tool_type:
        entry["type"] = tool_type
    header_data[tool_key] = entry
    return hex_id

# ─── Tool-ref file helpers ────────────────────────────────────────────────────
def tool_ref_path(tool_key: str) -> Path:
    return REF_DIR / f"{tool_key}.json"

def load_tool_ref(tool_key: str) -> dict:
    return load_json(tool_ref_path(tool_key))

def save_tool_ref(tool_key: str, data: dict):
    save_json(tool_ref_path(tool_key), data)

# ─── Argument resolution ─────────────────────────────────────────────────────
def resolve_tool(raw_args: list, normal_flag = True) -> tuple:
    """
    Join all non-flag tokens before first flag into a single tool name.
    Returns (tool_key, remaining_args).
    'hello world --topic foo' → ('helloworld', ['--topic', 'foo'])
    """
    tool_parts = []
    rest = []
    past_flags = False
    for a in raw_args:
        if a.startswith("--"):
            past_flags = True
        if past_flags:
            rest.append(a)
        else:
            tool_parts.append(a)
    """if tooll part is like ["ed", "dsd"] -> .join would "ed dsd" -> normalize -> eddsd"""
    if normal_flag is True:
        tool_key = normalise(" ".join(tool_parts)) if tool_parts else ""
    else :
        tool_key = " ".join(tool_parts) if tool_parts else ""
        
    return tool_key, rest
