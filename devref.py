"""
devref v2.1 - Personal Developer Reference CLI
"""

import sys
import os
import json
import re
import datetime
import subprocess
import tempfile
import textwrap
from pathlib import Path

# ─── Optional deps ────────────────────────────────────────────────────────────
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

# ─── Paths ────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    DEVREF_DIR = Path(sys.executable).parent
else:
    DEVREF_DIR = Path(__file__).resolve().parent

SRC_DIR    = DEVREF_DIR / "src"
REF_DIR    = DEVREF_DIR / "ref"
HEADER_FILE = SRC_DIR / "header.json"   # master index
NOTES_DIR  = DEVREF_DIR / "notes"       # --note files

SRC_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)

# ─── Color helpers ────────────────────────────────────────────────────────────
def c(text, color):
    if not HAS_COLOR:
        return str(text)
    colors = {
        "cyan":    Fore.CYAN,
        "green":   Fore.GREEN,
        "yellow":  Fore.YELLOW,
        "magenta": Fore.MAGENTA,
        "white":   Fore.WHITE,
        "blue":    Fore.BLUE,
        "bright":  Style.BRIGHT,
        "dim":     Style.DIM,
        "red":     Fore.RED,
    }
    return colors.get(color, "") + str(text) + Style.RESET_ALL

BOX = 60
def _center(text):
    pad = BOX - len(text)
    return " " * (pad // 2) + text + " " * (pad - pad // 2)

def section_header(text, color="cyan"):
    print(c(f"\n  {text}", color) + c("  " + "─" * (54 - len(text)), "dim"))

def header(text):
    width = 62
    print()
    print(c("─" * width, "cyan"))
    print(c(f"  {text}", "bright"))
    print(c("─" * width, "cyan"))

def label(text):
    print(c(f"\n  {text}", "yellow"))

def item(text, indent=4):
    prefix = " " * indent
    for line in textwrap.wrap(str(text), width=74 - indent):
        print(c(f"{prefix}{line}", "white"))

def syntax_item(text, indent=4):
    prefix = " " * indent
    print(c(f"{prefix}{text}", "green"))

def example_item(text, indent=4):
    prefix = " " * indent
    print(c(f"{prefix}{text}", "magenta"))

def usecase_item(text, indent=4):
    prefix = " " * indent
    print(c(f"{prefix}→ {text}", "blue"))

def hint_item(text, indent=4):
    prefix = " " * indent
    print(c(f"{prefix}e.g. {text}", "dim"))

def dim_print(text):
    print(c(f"  {text}", "dim"))

def success(text):
    print(c(f"\n  OK  {text}", "green"))

def warn(text):
    print(c(f"\n  !!  {text}", "yellow"))

def tip(text):
    print(c(f"\n  >>  {text}", "cyan"))

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

# ─── HEX ID helpers ──────────────────────────────────────────────────────────
def generate_hex_id() -> str:
    """Generate a 6-digit uppercase hex ID."""
    import random
    return format(random.randint(0, 0xFFFFFF), '06X')

def ids_equal(id1: str, id2: str) -> bool:
    """IDs are equal regardless of case."""
    return id1.upper() == id2.upper()

# ─── Tool name normalisation ─────────────────────────────────────────────────
def normalise(name: str) -> str:
    """
    Joins all words into a single lowercase string for comparison.
    'hello world' → 'helloworld'
    Also strips underscores and hyphens so 'g_it' == 'git'.
    """
    return re.sub(r'[\s_\-]', '', name).lower()

def fuzzy_name_match(query: str, candidate: str) -> bool:
    """
    Match tool names case-insensitively after stripping separators.
    'git' matches 'Git', 'G_it', 'g-it', 'GIT', etc.
    """
    return normalise(query) == normalise(candidate)

def find_tool_keys(query: str, header_data: dict) -> list:
    """Return all tool keys in header that match query (case/separator insensitive)."""
    matches = []
    for key in header_data.get("tools", []):
        if fuzzy_name_match(query, key):
            matches.append(key)
    return matches

# ─── Header (master index) helpers ───────────────────────────────────────────
def load_header() -> dict:
    data = load_json(HEADER_FILE)
    if "tools" not in data:
        data["tools"] = []
    return data

def save_header(data: dict):
    save_json(HEADER_FILE, data)

def get_tool_entry(header_data: dict, tool_key: str) -> dict:
    return header_data.get(tool_key, {})

def tool_ref_path(tool_key: str) -> Path:
    return REF_DIR / f"{tool_key}.json"

def load_tool_ref(tool_key: str) -> dict:
    return load_json(tool_ref_path(tool_key))

def save_tool_ref(tool_key: str, data: dict):
    save_json(tool_ref_path(tool_key), data)

def add_tool_to_header(header_data: dict, tool_key: str, description: str, tags: list) -> str:
    hex_id = generate_hex_id()
    header_data.setdefault("tools", [])
    if tool_key not in header_data["tools"]:
        header_data["tools"].append(tool_key)
    header_data[tool_key] = {
        "id": hex_id,
        "name": tool_key,
        "tags": tags,
        "description": description,
        "topics": []
    }
    return hex_id

def resolve_tool(raw_args: list) -> tuple:
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
    tool_key = normalise(" ".join(tool_parts)) if tool_parts else ""
    return tool_key, rest

# ─── Console editor ───────────────────────────────────────────────────────────
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
    edited = open_console_editor(content)
    try:
        return json.loads(edited)
    except json.JSONDecodeError as e:
        warn(f"Invalid JSON after editing: {e}")
        return None

# ─── Display helpers ──────────────────────────────────────────────────────────
def display_topic(tool: str, topic: str, data: dict):
    header(f"{tool.upper()}  →  {topic}")
    if "description" in data:
        label("Description")
        item(data["description"])
    if "what_it_does" in data:
        label("What it does")
        item(data["what_it_does"])
    if "use_cases" in data and data["use_cases"]:
        label("Use Cases")
        for u in data["use_cases"]:
            usecase_item(u)
    if "tags" in data and data["tags"]:
        label("Tags")
        item(", ".join(data["tags"]))
    if "syntax" in data and data["syntax"]:
        label("Syntax")
        for s in data["syntax"]:
            syntax_item(s)
    if "examples" in data and data["examples"]:
        label("Examples")
        for e in data["examples"]:
            example_item(e)
    print()

def display_tool_summary(tool_key: str, header_entry: dict, ref_data: dict):
    header(f"{header_entry.get('name', tool_key).upper()}  —  Overview")
    label("ID")
    item(header_entry.get("id", "N/A"))
    if header_entry.get("description"):
        label("Description")
        item(header_entry["description"])
    if header_entry.get("tags"):
        label("Tags")
        item(", ".join(header_entry["tags"]))
    topics = ref_data.get("topics", {})
    if topics:
        label("Topics")
        for t, tdata in topics.items():
            desc = tdata.get("description", "")
            short = (desc[:55] + "…") if len(desc) > 55 else desc
            print(c(f"    • {t}", "green") + c(f"  —  {short}", "dim"))
    print()
    tip(f"Run:  devref --find {tool_key} --topic <name>  to view a topic")

# ─── Wizard helpers ───────────────────────────────────────────────────────────
HINTS = {
    "tool_desc":    "High-level interpreted programming language",
    "tool_tags":    "language, scripting, data",
    "topic_name":   "venv  or  list-comprehension  or  pip",
    "topic_desc":   "Virtual environment to isolate project dependencies",
    "topic_what":   "Creates a self-contained Python environment per project",
    "topic_uc":     "Isolate packages per project  /  Avoid version conflicts",
    "syntax_entry": "python -m venv <env-name>",
    "example_entry":"python -m venv myenv",
}

def ask(prompt_text: str, hint: str = None) -> str:
    if hint:
        hint_item(hint)
    return input(c(f"  {prompt_text} ", "yellow")).strip()

def ask_list(label_text: str, hint: str = None) -> list:
    print(c(f"\n  {label_text}", "yellow") + c("  (blank line to finish)", "dim"))
    if hint:
        hint_item(hint)
    items = []
    while True:
        val = input(c("    > ", "cyan")).strip()
        if not val:
            break
        items.append(val)
    return items

def collect_topic_data() -> dict:
    desc = ask("Description:", hint=HINTS["topic_desc"])
    what = ask("What it does (Enter to skip):", hint=HINTS["topic_what"])
    ucs  = ask_list("Use cases (one per line)", hint=HINTS["topic_uc"])
    syns = ask_list("Syntax entries (one per line)", hint=HINTS["syntax_entry"])
    exps = ask_list("Examples (one per line)", hint=HINTS["example_entry"])
    tags_raw = ask("Tags (comma-separated, optional):", hint=HINTS["tool_tags"])
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    data = {"description": desc}
    if what: data["what_it_does"] = what
    if ucs:  data["use_cases"]    = ucs
    if syns: data["syntax"]       = syns
    if exps: data["examples"]     = exps
    if tags: data["tags"]         = tags
    return data

# ─── Help command ─────────────────────────────────────────────────────────────
def cmd_help():
    print()
    print(c("  ╔" + "═" * BOX + "╗", "cyan"))
    print(c("  ║", "cyan") + c(_center("devref  —  Developer Reference CLI"), "bright") + c("║", "cyan"))
    print(c("  ║", "cyan") + c(_center("v 2.1"), "dim")                                  + c("║", "cyan"))
    print(c("  ╚" + "═" * BOX + "╝", "cyan"))

    section_header("FINDING TOOLS & TOPICS", "yellow")
    rows = [
        ("devref --find <tool>",                        "Tool overview with topics"),
        ("devref --find <tool> --topic <name>",         "Full detail on a topic"),
        ("devref --find <tool> --tag <tag>",            "Search tags under that tool's topics"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("SEARCHING", "magenta")
    rows = [
        ("devref --search <tag>",                       "Search tags across ALL tool entries")
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("ADDING CONTENT", "cyan")
    rows = [
        ("devref --new <tool>",                         "New tool wizard (terminal)"),
        ("devref --new <tool> --notepad",               "New tool in console editor"),
        ("devref --add <tool> --topic <name>",          "Add topic via terminal wizard"),
        ("devref --add <tool> --topic <name> --notepad", "Add topic in console editor"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("EDITING", "yellow")
    rows = [
        ("devref --edit <tool>",                  "Edit tool name/description/tags"),
        ("devref --edit <tool> --topic <name>",   "Edit a topic in console editor"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("DELETING", "red")
    rows = [
        ("devref --del <tool>",                   "Delete entire tool entry"),
        ("devref --del <tool> --topic <name>",    "Delete one topic"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("AI PROMPT", "magenta")
    rows = [
        ("devref --prompt <tool>",                "Generate prompt for entire tool"),
        ("devref --find <tool> --prompt <topic>", "Generate prompt for one topic"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("IMPORT / EXPORT", "cyan")
    rows = [
        ("devref --export <tool>",                              "Export tool as single JSON file"),
        ("devref --import <file>",                              "Import a single exported JSON file"),
        ("devref --import <file> --tool <name>",                "Import file as a new tool (named)"),
        ("devref --import <file> --tool <name> --topic <file2>", "Create tool + add topic from file2"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<54}", "green") + c(desc, "dim"))

    section_header("NOTES", "blue")
    rows = [
        ("devref --note",                         "List all notes"),
        ("devref --note <name>",                  "Open/create note in console editor"),
        ("devref --note <name> --del",            "Delete a note"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("UTILS", "cyan")
    rows = [
        ("devref --list",                         "List all tools in reference"),
        ("devref --help",                         "Show this help"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))
    print()

# ─── Find command ─────────────────────────────────────────────────────────────
def cmd_find(raw_args: list):
    if not raw_args:
        warn("Usage: devref --find <tool>")
        return

    tool_query, rest = resolve_tool(raw_args)
    if not tool_query:
        warn("Usage: devref --find <tool>")
        return

    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)

    # ── Multiple matches (e.g. 'git' and 'Git' both exist)
    if len(matches) > 1:
        header("Multiple tools matched")
        for key in matches:
            entry = header_data[key]
            print()
            print(c(f"    ID: {entry.get('id','?')}", "yellow"))
            print(c(f"    {entry.get('name', key)}", "bright"))
            desc = entry.get("description", "")
            if desc:
                print(c(f"      {desc}", "dim"))
        print()
        tip("Use  devref --find <tool> --id <hex>  to select one specifically")
        return

    if not matches:
        warn(f"No tool found matching '{tool_query}'.")
        tip(f"Run:  devref --new {tool_query}  to create one")
        return

    tool_key = matches[0]
    header_entry = header_data[tool_key]
    ref_data = load_tool_ref(tool_key)

    # --find <tool> --tag <tag>  →  search tags within that tool's topics
    if "--tag" in rest:
        idx = rest.index("--tag")
        tag_parts = []
        for a in rest[idx + 1:]:
            if a.startswith("--"):
                break
            tag_parts.append(a)
        tag = normalise(" ".join(tag_parts))
        if not tag:
            warn("Provide a tag name.")
            return
        header(f"{tool_key.upper()}  —  Topics tagged '{tag}'")
        found = False
        for tname, tdata in ref_data.get("topics", {}).items():
            topic_tags = [normalise(t) for t in tdata.get("tags", [])]
            if tag in topic_tags:
                desc = tdata.get("description", "")
                print(c(f"    • {tname}", "green") + c(f"  —  {desc[:55]}", "dim"))
                found = True
        if not found:
            warn(f"No topics tagged '{tag}' under '{tool_key}'.")
        print()
        return

    # --find <tool> --prompt <topic>
    if "--prompt" in rest:
        idx = rest.index("--prompt")
        topic_parts = []
        for a in rest[idx + 1:]:
            if a.startswith("--"):
                break
            topic_parts.append(a)
        topic_name = normalise(" ".join(topic_parts))
        if not topic_name:
            warn("Provide a topic name: devref --find <tool> --prompt <topic>")
            return
        topic_data = ref_data.get("topics", {}).get(topic_name, None)
        if topic_data is None:
            warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
            return
        cmd_prompt_topic(tool_key, topic_name, topic_data, header_entry)
        return

    # --find <tool> --topic <name>
    if "--topic" in rest:
        idx = rest.index("--topic")
        topic_parts = []
        for a in rest[idx + 1:]:
            if a.startswith("--"):
                break
            topic_parts.append(a)
        topic_name = normalise(" ".join(topic_parts))
        if topic_name:
            topics = ref_data.get("topics", {})
            if topic_name in topics:
                display_topic(tool_key, topic_name, topics[topic_name])
            else:
                warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
                tip(f"Run:  devref --find {tool_key}  to see all topics")
        else:
            display_tool_summary(tool_key, header_entry, ref_data)
        return

    # Plain --find <tool>
    display_tool_summary(tool_key, header_entry, ref_data)

# ─── Search (tag-based) ───────────────────────────────────────────────────────
def cmd_search(raw_args: list):
    """devref --search <tag>  — search tags across all tools."""
    tag_parts = [a for a in raw_args if not a.startswith("--")]
    tag = normalise(" ".join(tag_parts))
    if not tag:
        warn('Usage: devref --search <tag>')
        return

    header_data = load_header()
    header(f'Tag search: "{tag}"')
    found = False
    for tool_key in header_data.get("tools", []):
        ref_data = load_tool_ref(tool_key)
        tool_entry = header_data.get(tool_key, {})
        # Check tool-level tags
        tool_tags = [normalise(t) for t in tool_entry.get("tags", [])]
        if tag in tool_tags:
            print(c(f"    {tool_key}", "yellow") + c("  [tool tag]", "dim"))
            found = True
        # Check topic-level tags
        for tname, tdata in ref_data.get("topics", {}).items():
            topic_tags = [normalise(t) for t in tdata.get("tags", [])]
            if tag in topic_tags:
                print(c(f"    {tool_key}", "yellow") + " → " + c(tname, "green") + c("  [topic tag]", "dim"))
                found = True
    if not found:
        warn(f"No entries tagged '{tag}'.")
    print()

# ─── New command ──────────────────────────────────────────────────────────────
def cmd_new(raw_args: list):
    if not raw_args:
        warn("Usage: devref --new <tool>")
        return

    tool_query, rest = resolve_tool(raw_args)
    use_notepad = "--notepad" in rest

    if not tool_query:
        warn("Usage: devref --new <tool>")
        return

    header_data = load_header()
    existing = find_tool_keys(tool_query, header_data)
    if existing:
        warn(f"'{tool_query}' already exists. Use  devref --add {tool_query} --topic <name>  instead.")
        return

    tool_key = tool_query  # normalised name used as key

    if use_notepad:
        # Build template matching the new json syntax
        template = {
            "id": generate_hex_id(),
            "name": tool_key,
            "topics": {
                "example-topic": {
                    "name": "example-topic",
                    "tags": ["tag1"],
                    "description": "What this topic is about",
                    "what_it_does": "Detailed explanation",
                    "syntax": ["command --flag <required>"],
                    "examples": ["command --flag value"]
                }
            }
        }
        content = json.dumps(template, indent=2, ensure_ascii=False)
        edited = open_console_editor(content)
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
    tags_raw = ask("Tags (comma-separated):", hint=HINTS["tool_tags"])
    tags     = [t.strip() for t in tags_raw.split(",") if t.strip()]

    hex_id = add_tool_to_header(header_data, tool_key, desc, tags)
    ref_data = {"id": hex_id, "name": tool_key, "topics": {}}

    print(c("\n  Now add topics. Blank topic name to finish.", "cyan"))
    while True:
        tname_raw = ask("\n  Topic name (blank to finish):", hint=HINTS["topic_name"])
        if not tname_raw:
            break
        tname = normalise(tname_raw)
        tdata = collect_topic_data()
        ref_data["topics"][tname] = tdata
        header_data[tool_key]["topics"].append(tname)

    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"'{tool_key}' added!")
    tip(f"Run:  devref --find {tool_key}")

def _apply_new_tool_from_parsed(tool_key: str, parsed: dict, header_data: dict):
    """Save a new tool from a parsed dict (notepad flow)."""
    desc = parsed.get("description", "")
    tags = parsed.get("tags", [])
    topics_dict = parsed.get("topics", {})
    topic_keys = list(topics_dict.keys())
    hex_id = parsed.get("id") or generate_hex_id()

    header_data.setdefault("tools", [])
    if tool_key not in header_data["tools"]:
        header_data["tools"].append(tool_key)
    header_data[tool_key] = {
        "id": hex_id,
        "name": tool_key,
        "tags": tags,
        "description": desc,
        "topics": topic_keys
    }
    ref_data = {"id": hex_id, "name": tool_key, "topics": topics_dict}
    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"'{tool_key}' created from editor!")
    tip(f"Run:  devref --find {tool_key}")

# ─── Add command ──────────────────────────────────────────────────────────────
def cmd_add(raw_args: list):
    if not raw_args:
        warn("Usage: devref --add <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args)
    use_notepad = "--notepad" in rest

    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"'{tool_query}' not found. Run  devref --new {tool_query}  first.")
        return
    tool_key = matches[0]

    if "--topic" not in rest:
        warn("Usage: devref --add <tool> --topic <name>")
        return

    idx = rest.index("--topic")
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
                "name": topic_name,
                "tags": [],
                "description": "What this topic is about",
                "what_it_does": "Detailed explanation",
                "syntax": ["command --flag <required>"],
                "examples": ["command --flag value"]
            }
        }
        content = json.dumps(template, indent=2, ensure_ascii=False)
        edited = open_console_editor(content)
        try:
            parsed = json.loads(edited)
        except json.JSONDecodeError as e:
            warn(f"Invalid JSON: {e}")
            return

        # parsed may contain one or more topics
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
    tdata = collect_topic_data()
    ref_data.setdefault("topics", {})[topic_name] = tdata
    header_data[tool_key].setdefault("topics", [])
    if topic_name not in header_data[tool_key]["topics"]:
        header_data[tool_key]["topics"].append(topic_name)
    save_header(header_data)
    save_tool_ref(tool_key, ref_data)
    success(f"Topic '{topic_name}' added to '{tool_key}'!")

# ─── Edit command ─────────────────────────────────────────────────────────────
def cmd_edit(raw_args: list):
    if not raw_args:
        warn("Usage: devref --edit <tool>  OR  devref --edit <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args)
    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"Tool '{tool_query}' not found.")
        return
    tool_key = matches[0]

    if "--topic" in rest:
        # Edit topic in console editor
        idx = rest.index("--topic")
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
        topics = ref_data.get("topics", {})
        if topic_name not in topics:
            warn(f"Topic '{topic_name}' not found under '{tool_key}'.")
            return
        current = topics[topic_name]
        edited = open_console_editor_json(current)
        if edited is None:
            return
        topics[topic_name] = edited
        ref_data["topics"] = topics
        save_tool_ref(tool_key, ref_data)
        success(f"Topic '{topic_name}' updated!")
        return

    # Edit tool-level fields: name, description, tags only
    entry = header_data[tool_key]
    editable = {
        "name":        entry.get("name", tool_key),
        "description": entry.get("description", ""),
        "tags":        entry.get("tags", []),
    }
    edited = open_console_editor_json(editable)
    if edited is None:
        return
    entry["name"]        = edited.get("name", entry["name"])
    entry["description"] = edited.get("description", entry["description"])
    entry["tags"]        = edited.get("tags", entry["tags"])
    header_data[tool_key] = entry
    save_header(header_data)
    success(f"Tool '{tool_key}' updated!")

# ─── Delete command ───────────────────────────────────────────────────────────
def cmd_del(raw_args: list):
    if not raw_args:
        warn("Usage: devref --del <tool>  OR  devref --del <tool> --topic <name>")
        return

    tool_query, rest = resolve_tool(raw_args)
    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"Tool '{tool_query}' not found.")
        return
    tool_key = matches[0]

    if "--topic" in rest:
        idx = rest.index("--topic")
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

# ─── List command ─────────────────────────────────────────────────────────────
def cmd_list():
    header_data = load_header()
    tools = header_data.get("tools", [])
    if not tools:
        warn("No entries yet. Run  devref --new <tool>  to start.")
        return
    header("All Tools in Reference")
    for tool_key in sorted(tools):
        entry = header_data.get(tool_key, {})
        desc  = entry.get("description", "")
        short = (desc[:48] + "…") if len(desc) > 48 else desc
        tid   = entry.get("id", "??????")
        topics = entry.get("topics", [])
        print(c(f"    [{tid}]", "yellow") + "  " + c(entry.get("name", tool_key), "bright") +
              c(f"  [{len(topics)} topics]", "dim"))
        if short:
            print(c(f"        {short}", "dim"))
    print()

# ─── Prompt command ───────────────────────────────────────────────────────────
def cmd_prompt(raw_args: list):
    if not raw_args:
        warn("Usage: devref --prompt <tool>")
        return

    tool_query, _ = resolve_tool(raw_args)
    tool = tool_query

    header_data = load_header()
    matches = find_tool_keys(tool, header_data)
    tool_display = matches[0] if matches else tool

    prompt_text = f"""
Generate a tool reference entry for devref for the tool: "{tool_display}"

Use EXACTLY this JSON structure — raw JSON only, no markdown fences, no preamble:

{{
  "id": "AUTO",
  "name": "{tool_display}",
  "topics": {{
    "topic-name": {{
      "name": "topic-name",
      "tags": ["tag1", "tag2"],
      "description": "What this topic is about",
      "what_it_does": "Detailed explanation of behavior",
      "use_cases": [
        "Use this when doing X",
        "Prefer this over Y when Z"
      ],
      "syntax": [
        "command --flag <required>",
        "command --flag <required> [optional]"
      ],
      "examples": [
        "real working example",
        "another concrete example"
      ]
    }}
  }}
}}

Requirements:
- Cover at least 6 of the most commonly used topics for "{tool_display}"
- Descriptions: concise and accurate
- Syntax: use <angle-brackets> for required args and [brackets] for optional
- Use cases: specific and actionable
- Multiple topics may be included in this single file — add as many topic blocks as needed
- Output raw JSON only — no explanation, preamble or markdown fences
- Don't use these kind of naming conventions: firstname-lastname rather use firstnamelastname 
"""
    header(f"AI Prompt  —  {tool_display.upper()}")
    print(c(prompt_text, "white"))
    tip("Paste into Claude/ChatGPT → copy returned JSON → save as file.json")
    tip(f"Then run:  devref --import file.json --tool {tool_display}")

def cmd_prompt_topic(tool_key: str, topic_name: str, topic_data: dict, header_entry: dict):
    """Print prompt for a single topic. Multiple topics hint included."""
    header(f"AI Prompt  —  {tool_key.upper()}  →  {topic_name}")
    prompt_text = f"""
You are populating a developer reference entry.
Tool: "{header_entry.get('name', tool_key)}"
Topic: "{topic_name}"

Current data:
{json.dumps(topic_data, indent=2)}

Improve, fill in missing fields, or generate new content for this topic.
Multiple related topics may be included in one file — add extra topic blocks freely.

Output ONLY raw JSON with this structure (no markdown fences, no preamble):

{{
  "{topic_name}": {{
    "name": "{topic_name}",
    "tags": ["tag1"],
    "description": "...",
    "what_it_does": "...",
    "use_cases": ["..."],
    "syntax": ["command --flag <required>"],
    "examples": ["example here"]
  }},
  "optional-extra-topic": {{ ... }}
}}
"""
    print(c(prompt_text, "white"))
    tip(f"Paste into AI → save result → run:  devref --import result.json --tool {tool_key} --topic result.json")

# ─── Export command ───────────────────────────────────────────────────────────
def cmd_export(raw_args: list):
    if not raw_args:
        warn("Usage: devref --export <tool>")
        return

    tool_query, _ = resolve_tool(raw_args)
    header_data = load_header()
    matches = find_tool_keys(tool_query, header_data)
    if not matches:
        warn(f"Tool '{tool_query}' not found.")
        return
    tool_key = matches[0]

    header_entry = header_data[tool_key]
    ref_data     = load_tool_ref(tool_key)

    export_data = {
        "id":          header_entry.get("id"),
        "name":        header_entry.get("name", tool_key),
        "description": header_entry.get("description", ""),
        "tags":        header_entry.get("tags", []),
        "topics":      ref_data.get("topics", {})
    }

    out = DEVREF_DIR / f"{tool_key}_export.json"
    save_json(out, export_data)
    success(f"Exported to: {out}")

# ─── Import command ───────────────────────────────────────────────────────────
def cmd_import(raw_args: list):
    """
    devref --import <file>                         → auto-detect as full tool export
    devref --import <file> --tool <name>           → import file as new tool named <name>
    devref --import <file> --tool <name> --topic <file2>  → create tool + add topic from file2
    """
    if not raw_args:
        warn("Usage: devref --import <file>  [--tool <name>]  [--topic <file2>]")
        return

    src_path = Path(raw_args[0])
    if not src_path.exists():
        warn(f"File not found: {src_path}")
        return

    # Parse --tool <name>
    tool_name = None
    if "--tool" in raw_args:
        idx = raw_args.index("--tool")
        tool_parts = []
        for a in raw_args[idx + 1:]:
            if a.startswith("--"):
                break
            tool_parts.append(a)
        tool_name = normalise(" ".join(tool_parts)) if tool_parts else None

    # Parse --topic <file2>
    topic_file = None
    if "--topic" in raw_args:
        idx = raw_args.index("--topic")
        if idx + 1 < len(raw_args) and not raw_args[idx + 1].startswith("--"):
            topic_file = Path(raw_args[idx + 1])

    try:
        new_data = load_json(src_path)
    except Exception as e:
        warn(f"Could not parse JSON: {e}")
        return

    if not isinstance(new_data, dict) or not new_data:
        warn("Empty or invalid JSON.")
        return

    header_data = load_header()

    if tool_name and topic_file:
        # Create tool from src_path; add topic(s) from topic_file
        _import_as_new_tool(header_data, tool_name, new_data)
        try:
            topic_data = load_json(topic_file)
        except Exception as e:
            warn(f"Could not parse topic file: {e}")
            return
        _import_topics_into_tool(header_data, tool_name, topic_data)
        return

    if tool_name:
        # Import src_path as a new tool
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
        # Merge topics
        real_key = existing[0]
        ref_data = load_tool_ref(real_key)
        count = 0
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

    desc   = data.get("description", "")
    tags   = data.get("tags", [])
    topics = data.get("topics", {})
    hex_id = data.get("id") or generate_hex_id()

    header_data.setdefault("tools", []).append(tool_key)
    header_data[tool_key] = {
        "id":          hex_id,
        "name":        data.get("name", tool_key),
        "tags":        tags,
        "description": desc,
        "topics":      list(topics.keys())
    }
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
    count = 0

    # topic_data may be {topic_name: {...}} directly, or {"topics": {topic_name: {...}}}
    topics_dict = topic_data.get("topics", topic_data)
    for tname, tdata in topics_dict.items():
        if tname in ("id", "name", "description", "tags"):
            continue
        norm = normalise(tname)
        ref_data.setdefault("topics", {})[norm] = tdata
        if norm not in header_data[real_key].get("topics", []):
            header_data[real_key].setdefault("topics", []).append(norm)
        count += 1

    save_tool_ref(real_key, ref_data)
    save_header(header_data)
    success(f"Added {count} topic(s) to '{real_key}'.")

# ─── Notes command ────────────────────────────────────────────────────────────
def cmd_note(raw_args: list):
    """
    devref --note              → list all notes
    devref --note <name>       → open/create note in console editor
    devref --note <name> --del → delete note
    """
    name_parts = [a for a in raw_args if not a.startswith("--")]
    name = normalise(" ".join(name_parts)) if name_parts else ""
    do_del = "--del" in raw_args

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

# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        cmd_help()
        return

    cmd  = argv[0].lower()
    rest = argv[1:]

    dispatch = {
        "--find":   lambda: cmd_find(rest),
        "--search": lambda: cmd_search(rest),
        "--new":    lambda: cmd_new(rest),
        "--add":    lambda: cmd_add(rest),
        "--edit":   lambda: cmd_edit(rest),
        "--del":    lambda: cmd_del(rest),
        "--list":   lambda: cmd_list(),
        "--export": lambda: cmd_export(rest),
        "--import": lambda: cmd_import(rest),
        "--prompt": lambda: cmd_prompt(rest),
        "--note":   lambda: cmd_note(rest),
    }

    if cmd in dispatch:
        dispatch[cmd]()
    else:
        warn(f"Unknown command: {cmd}")
        tip("Run  devref --help  for usage")

if __name__ == "__main__":
    main()
