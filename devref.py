"""
devref v2.0 - Personal Developer Reference CLI
"""

import sys
import os
import json
import datetime
import subprocess
import textwrap
from pathlib import Path

# ─── Optional deps ────────────────────────────────────────────────────────────
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

try:
    from rapidfuzz import fuzz
    HAS_FUZZ = True
except ImportError:
    HAS_FUZZ = False

try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter, Completer, Completion
    from prompt_toolkit.styles import Style as PtStyle
    from prompt_toolkit.formatted_text import HTML
    HAS_PT = True
except ImportError:
    HAS_PT = False

# ─── Paths ────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    DEVREF_DIR = Path(sys.executable).parent
else:
    DEVREF_DIR = Path(__file__).resolve().parent

REF_DIR    = DEVREF_DIR / "ref"
TOOLS_FILE = REF_DIR / "tools.json"      # was ref.json
SNIP_FILE  = REF_DIR / "snippets.json"   # was syntax.json
META_FILE  = REF_DIR / "meta.json"

# Legacy migration: if old names exist but new don't, rename them
def _migrate_legacy():
    old_ref = REF_DIR / "ref.json"
    old_syn = REF_DIR / "syntax.json"
    if old_ref.exists() and not TOOLS_FILE.exists():
        old_ref.rename(TOOLS_FILE)
    if old_syn.exists() and not SNIP_FILE.exists():
        old_syn.rename(SNIP_FILE)

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
    }
    return colors.get(color, "") + str(text) + Style.RESET_ALL

def section_header(text, color="cyan"):
    """Colored section headers inside --help"""
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

# ─── Settings ─────────────────────────────────────────────────────────────────
def load_settings() -> dict:
    meta = load_json(META_FILE)
    return meta.get("settings", {"hints": True})

def save_settings(settings: dict):
    meta = load_json(META_FILE)
    meta["settings"] = settings
    save_json(META_FILE, meta)

def hints_on() -> bool:
    return load_settings().get("hints", True)

# ─── Recent history ───────────────────────────────────────────────────────────
def record_recent(query: str):
    meta = load_json(META_FILE)
    recent = meta.get("recent", [])
    entry = {"query": query, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    recent = [r for r in recent if r["query"] != query]
    recent.insert(0, entry)
    meta["recent"] = recent[:20]
    save_json(META_FILE, meta)

# ─── Autocomplete input ───────────────────────────────────────────────────────
def smart_input(prompt_text: str, completions: list = None, hint: str = None) -> str:
    """Input with optional autocomplete and hint display."""
    show_hints = hints_on()
    if show_hints and hint:
        hint_item(hint)

    if HAS_PT and completions:
        completer = WordCompleter(completions, ignore_case=True)
        pt_style = PtStyle.from_dict({"prompt": "ansiyellow bold", "": "ansiwhite"})
        try:
            return pt_prompt(
                HTML(f"<prompt>  {prompt_text} </prompt>"),
                completer=completer,
                style=pt_style,
                complete_while_typing=True,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            return ""
    else:
        return input(c(f"  {prompt_text} ", "yellow")).strip()

def smart_collect_list(label_text: str, hint: str = None) -> list:
    """Collect multiple items with optional hint. Blank line finishes."""
    show_hints = hints_on()
    print(c(f"\n  {label_text}", "yellow") + c("  (blank line to finish)", "dim"))
    if show_hints and hint:
        hint_item(hint)
    items = []
    while True:
        val = input(c("    > ", "cyan")).strip()
        if not val:
            break
        items.append(val)
    return items

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

def display_snippet_entry(tool: str, name: str, data: dict):
    header(f"SNIPPET  {tool.upper()}  →  {name}")
    if "description" in data:
        label("Description")
        item(data["description"])
    if "use_cases" in data and data["use_cases"]:
        label("Use Cases")
        for u in data["use_cases"]:
            usecase_item(u)
    if "pattern" in data:
        label("Pattern")
        syntax_item(data["pattern"])
    if "examples" in data and data["examples"]:
        label("Examples")
        for e in data["examples"]:
            example_item(e)
    print()

def display_tool_summary(tool: str, data: dict):
    header(f"{tool.upper()}  —  Overview")
    if "description" in data:
        label("Description")
        item(data["description"])
    if "use_cases" in data and data["use_cases"]:
        label("Use Cases")
        for u in data["use_cases"]:
            usecase_item(u)
    if "tags" in data and data["tags"]:
        label("Tags")
        item(", ".join(data["tags"]))
    topics = data.get("topics", {})
    if topics:
        label("Topics")
        for t in topics:
            desc = topics[t].get("description", "")
            short = (desc[:58] + "…") if len(desc) > 58 else desc
            print(c(f"    • {t}", "green") + c(f"  —  {short}", "dim"))
    print()
    tip(f"Run:  devref --find {tool} --topic <name>  to view a topic")
    tip(f"Run:  devref --find {tool} --snippets      to view snippets")

# ─── Help command ─────────────────────────────────────────────────────────────
def cmd_help():
    print()
    print(c("  ╔══════════════════════════════════════════════════════════╗", "cyan"))
    print(c("  ║", "cyan") + c("          devref  —  Developer Reference CLI          ", "bright") + c("║", "cyan"))
    print(c("  ║", "cyan") + c("                      v 2.0                           ", "dim") + c("║", "cyan"))
    print(c("  ╚══════════════════════════════════════════════════════════╝", "cyan"))

    section_header("FINDING CONTENT", "yellow")
    rows = [
        ("devref --find <tool>",                  "Tool overview + all topics"),
        ("devref --find <tool> --topic <name>",   "Full detail on a topic"),
        ("devref --find <tool> --snippets",        "List all snippet entries"),
        ("devref --find <tool> --snippets <name>", "Show one snippet entry"),
        ("devref --find --tag <tag>",              "Find all entries with tag"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<42}", "green") + c(desc, "dim"))

    section_header("SEARCHING", "magenta")
    rows = [
        ("devref --search \"<text>\"",                     "Search across everything"),
        ("devref --search \"<text>\" --tools",             "Search tools file only"),
        ("devref --search \"<text>\" --snippets",          "Search snippets file only"),
        ("devref --find <tool> --search \"<text>\"",       "Search within one tool"),
        ("devref --find <tool> --search \"<text>\" --topics",    "Search topics only"),
        ("devref --find <tool> --search \"<text>\" --snippets",  "Search snippets only"),
        ("devref --find <tool> --search \"<text>\" --usecases",  "Search use cases only"),
        ("devref --find <tool> --search \"<text>\" --examples",  "Search examples only"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<50}", "green") + c(desc, "dim"))

    section_header("ADDING CONTENT", "cyan")
    rows = [
        ("devref --new <tool>",                   "New tool wizard (terminal)"),
        ("devref --new <tool> --notepad",          "New tool template in Notepad"),
        ("devref --add <tool> --topic",            "Add topic to existing tool"),
        ("devref --add <tool> --snippets",         "Add snippet to existing tool"),
        ("devref --add <tool> --topic --notepad",  "Topic template in Notepad"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<42}", "green") + c(desc, "dim"))

    section_header("EDITING & DELETING", "yellow")
    rows = [
        ("devref --edit <tool> --topic <name>",    "Edit topic (type name to confirm)"),
        ("devref --edit <tool> --snippets <name>", "Edit a snippet entry"),
        ("devref --delete <tool>",                 "Delete entire tool entry"),
        ("devref --delete <tool> --topic <name>",  "Delete one topic"),
        ("devref --delete <tool> --snippets <n>",  "Delete one snippet"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<44}", "green") + c(desc, "dim"))

    section_header("TAGS", "blue")
    rows = [
        ("devref --tag <tool> <topic> \"<tag>\"",  "Tag a topic"),
        ("devref --find --tag \"<tag>\"",           "Find all entries with tag"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<42}", "green") + c(desc, "dim"))

    section_header("AI PROMPT", "magenta")
    rows = [
        ("devref --prompt <tool>",           "Prompt for both files"),
        ("devref --prompt <tool> --tools",   "Prompt for tools.json only"),
        ("devref --prompt <tool> --snippets","Prompt for snippets.json only"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<42}", "green") + c(desc, "dim"))

    section_header("SETTINGS & UTILS", "cyan")
    rows = [
        ("devref --set hints on",    "Enable wizard example hints"),
        ("devref --set hints off",   "Disable wizard example hints"),
        ("devref --list",            "List all tools in reference"),
        ("devref --recent",          "Show last 10 lookups"),
        ("devref --backup",          "Backup JSON files (timestamped)"),
        ("devref --export <tool>",   "Export tool as Markdown"),
        ("devref --import <file>",   "Merge external JSON into tools"),
        ("devref --help",            "Show this help"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<42}", "green") + c(desc, "dim"))
    print()

# ─── Find command ─────────────────────────────────────────────────────────────
def cmd_find(args):
    tool = args[0].lower() if args else None
    if not tool:
        warn("Usage: devref --find <tool>")
        return

    tools = load_json(TOOLS_FILE)
    snips = load_json(SNIP_FILE)

    # --find python --snippets [name]
    if "--snippets" in args:
        idx = args.index("--snippets")
        snip_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None
        tool_snips = snips.get(tool, {}).get("entries", {})
        if not tool_snips:
            warn(f"No snippets found for '{tool}'.")
            return
        if snip_name:
            key = snip_name.lower()
            if key in tool_snips:
                record_recent(f"--find {tool} --snippets {key}")
                display_snippet_entry(tool, key, tool_snips[key])
            else:
                warn(f"Snippet '{snip_name}' not found under '{tool}'.")
                tip(f"Run:  devref --find {tool} --snippets  to see all")
        else:
            record_recent(f"--find {tool} --snippets")
            header(f"{tool.upper()}  —  Snippets")
            for name, entry in tool_snips.items():
                desc = entry.get("description", "")
                short = (desc[:58] + "…") if len(desc) > 58 else desc
                print(c(f"    • {name}", "green") + c(f"  —  {short}", "dim"))
            print()
            tip(f"Run:  devref --find {tool} --snippets <name>  for details")
        return

    # --find python --search "text" [--topics|--snippets|--usecases|--examples]
    if "--search" in args:
        idx = args.index("--search")
        query = args[idx + 1] if idx + 1 < len(args) else ""
        query = query.strip('"\'')
        # Determine sub-scope
        sub_scope = None
        for flag in ("--topics", "--snippets", "--usecases", "--examples"):
            if flag in args:
                sub_scope = flag.lstrip("-")
                break
        cmd_search([query], scope=tool, sub_scope=sub_scope)
        return

    # --find python --topic [name]
    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None
        tool_data = tools.get(tool)
        if not tool_data:
            warn(f"No reference found for '{tool}'.")
            tip("Run:  devref --new " + tool + "  to create one")
            return
        if topic_name:
            topics = tool_data.get("topics", {})
            key = topic_name.lower()
            if key in topics:
                record_recent(f"--find {tool} --topic {key}")
                display_topic(tool, key, topics[key])
            else:
                warn(f"Topic '{topic_name}' not found under '{tool}'.")
                tip(f"Run:  devref --find {tool}  to see all topics")
        else:
            record_recent(f"--find {tool}")
            display_tool_summary(tool, tool_data)
        return

    # --find python (plain)
    tool_data = tools.get(tool)
    if not tool_data:
        warn(f"No tools entry found for '{tool}'.")
        tip("Run:  devref --new " + tool + "  to create one")
        return
    record_recent(f"--find {tool}")
    display_tool_summary(tool, tool_data)

# ─── Search command ───────────────────────────────────────────────────────────
def cmd_search(args, scope=None, sub_scope=None):
    """
    scope     = tool name (search only inside that tool)
    sub_scope = "topics" | "snippets" | "usecases" | "examples"
                or None = search everything
    File-level flags: --tools, --snippets (no scope)
    """
    # Parse args for file-level scope flags
    file_scope = None  # "tools" | "snippets" | None
    clean_args = []
    for a in args:
        if a == "--tools":
            file_scope = "tools"
        elif a == "--snippets" and scope is None:
            file_scope = "snippets"
        else:
            clean_args.append(a)
    args = clean_args

    query = args[0].strip('"\'') if args else ""
    if not query:
        warn('Usage: devref --search "<text>"')
        return

    tools_db = load_json(TOOLS_FILE)
    snips_db = load_json(SNIP_FILE)

    results = []

    all_tool_names = list(dict.fromkeys(list(tools_db.keys()) + list(snips_db.keys())))
    target_tools = [scope] if scope else all_tool_names

    def fuzzy(blob: str) -> int:
        if HAS_FUZZ:
            return fuzz.partial_ratio(query.lower(), blob.lower())
        return 100 if query.lower() in blob.lower() else 0

    for tool in target_tools:
        # ── Search tools.json topics
        if file_scope in (None, "tools"):
            tool_data = tools_db.get(tool, {})
            for tname, tdata in tool_data.get("topics", {}).items():

                if sub_scope in (None, "topics"):
                    blob = " ".join([tname, tdata.get("description",""), tdata.get("what_it_does",""), " ".join(tdata.get("tags",[]))])
                    sc = fuzzy(blob)
                    if sc >= 60:
                        results.append((sc, "topic", tool, tname, tdata.get("description","")))

                if sub_scope in (None, "usecases"):
                    for uc in tdata.get("use_cases", []):
                        sc = fuzzy(uc)
                        if sc >= 60:
                            results.append((sc, "usecase", tool, tname, uc))

                if sub_scope in (None, "examples"):
                    for ex in tdata.get("examples", []):
                        sc = fuzzy(ex)
                        if sc >= 60:
                            results.append((sc, "example", tool, tname, ex))

        # ── Search snippets.json
        if file_scope in (None, "snippets"):
            for sname, sdata in snips_db.get(tool, {}).get("entries", {}).items():

                if sub_scope in (None, "snippets", "topics"):
                    blob = " ".join([sname, sdata.get("description",""), sdata.get("pattern","")])
                    sc = fuzzy(blob)
                    if sc >= 60:
                        results.append((sc, "snippet", tool, sname, sdata.get("description","")))

                if sub_scope in (None, "usecases"):
                    for uc in sdata.get("use_cases", []):
                        sc = fuzzy(uc)
                        if sc >= 60:
                            results.append((sc, "snippet-usecase", tool, sname, uc))

                if sub_scope in (None, "examples"):
                    for ex in sdata.get("examples", []):
                        sc = fuzzy(ex)
                        if sc >= 60:
                            results.append((sc, "snippet-example", tool, sname, ex))

    # Deduplicate by (type, tool, name)
    seen = set()
    unique = []
    for r in results:
        key = (r[1], r[2], r[3])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    results = sorted(unique, key=lambda x: x[0], reverse=True)

    if not results:
        warn(f"No results for '{query}'.")
        return

    scope_label = ""
    if scope:     scope_label += f"  in:{scope}"
    if sub_scope: scope_label += f"  [{sub_scope}]"
    if file_scope:scope_label += f"  [file:{file_scope}]"

    header(f'Search: "{query}"' + scope_label)

    kind_colors = {
        "topic":          "cyan",
        "usecase":        "blue",
        "example":        "magenta",
        "snippet":        "green",
        "snippet-usecase":"blue",
        "snippet-example":"magenta",
    }

    for score, kind, tool_name, name, desc in results:
        short = (desc[:55] + "…") if len(desc) > 55 else desc
        kc = kind_colors.get(kind, "white")
        print(
            c(f"    {tool_name}", "yellow") + " → " +
            c(name, "green") +
            c(f"  [{kind}]", kc) +
            c(f"  {score}%", "dim")
        )
        if short:
            print(c(f"        {short}", "dim"))
    print()
    tip("devref --find <tool> --topic <name>  or  --snippets <name>  to view")

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
    "snip_name":    "f-string  or  lambda  or  try-except",
    "snip_desc":    "Format strings with embedded expressions",
    "snip_pattern": 'f"text {<variable>} text"',
    "snip_uc":      "Build readable log messages  /  Format user-facing output",
}

def wizard_topic_entry() -> tuple:
    """Returns (name, data) for one topic."""
    tools_db = load_json(TOOLS_FILE)
    all_names = []
    for td in tools_db.values():
        all_names.extend(td.get("topics", {}).keys())

    name = smart_input("Topic name:", completions=all_names, hint=HINTS["topic_name"])
    desc = smart_input("Description:", hint=HINTS["topic_desc"])
    what = smart_input("What it does (Enter to skip):", hint=HINTS["topic_what"])
    ucs  = smart_collect_list("Use cases (one per line)", hint=HINTS["topic_uc"])
    syns = smart_collect_list("Syntax entries (one per line)", hint=HINTS["syntax_entry"])
    exps = smart_collect_list("Examples (one per line)", hint=HINTS["example_entry"])
    tags_raw = smart_input("Tags (comma-separated, optional):", hint=HINTS["tool_tags"])
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    data = {"description": desc}
    if what: data["what_it_does"] = what
    if ucs:  data["use_cases"]    = ucs
    if syns: data["syntax"]       = syns
    if exps: data["examples"]     = exps
    if tags: data["tags"]         = tags
    return name.lower(), data

def open_notepad(path: Path):
    subprocess.Popen(["notepad.exe", str(path)])
    tip(f"Opened in Notepad: {path}")
    tip("Save and close, then run:  devref --import <path>")

# ─── New command ──────────────────────────────────────────────────────────────
def cmd_new(args):
    if not args:
        warn("Usage: devref --new <tool>")
        return

    tools_db = load_json(TOOLS_FILE)
    all_tool_names = sorted(tools_db.keys())

    tool = args[0].lower()
    use_notepad = "--notepad" in args

    if tool in tools_db:
        warn(f"'{tool}' already exists. Use  devref --add {tool} --topic  instead.")
        return

    if use_notepad:
        template = {tool: {
            "description": "Describe this tool here",
            "tags": ["tag1"],
            "use_cases": ["When you need to do X", "As an alternative to Y"],
            "topics": {
                "example-topic": {
                    "description": "What this topic is about",
                    "what_it_does": "Detailed explanation",
                    "use_cases": ["Use when doing X"],
                    "syntax": ["command --flag"],
                    "examples": ["command --flag value"],
                    "tags": []
                }
            }
        }}
        tmp = REF_DIR / f"_new_{tool}.json"
        save_json(tmp, template)
        open_notepad(tmp)
        tip(f"After editing, run:  devref --import {tmp}")
        return

    print(c(f"\n  Creating new tool: {tool.upper()}", "bright"))
    desc     = smart_input("Tool description:", hint=HINTS["tool_desc"])
    ucs      = smart_collect_list("Tool-level use cases (one per line)", hint=HINTS["topic_uc"])
    tags_raw = smart_input("Tags (comma-separated):", hint=HINTS["tool_tags"])
    tags     = [t.strip() for t in tags_raw.split(",") if t.strip()]

    topics = {}
    print(c("\n  Now add topics. Blank topic name to finish.", "cyan"))
    while True:
        tname = smart_input("\n  Topic name (blank to finish):", completions=[], hint=HINTS["topic_name"])
        if not tname:
            break
        _, tdata = wizard_topic_entry()
        # name was re-entered inside wizard_topic_entry; use the one from here
        topics[tname.lower()] = tdata

    entry = {"description": desc}
    if ucs:    entry["use_cases"] = ucs
    if tags:   entry["tags"]      = tags
    if topics: entry["topics"]    = topics

    tools_db[tool] = entry
    save_json(TOOLS_FILE, tools_db)
    success(f"'{tool}' added to tools.json!")
    tip(f"Run:  devref --find {tool}")

# ─── Add command ──────────────────────────────────────────────────────────────
def cmd_add(args):
    if len(args) < 2:
        warn("Usage: devref --add <tool> --topic  OR  devref --add <tool> --snippets")
        return
    tool = args[0].lower()
    use_notepad = "--notepad" in args

    if "--topic" in args:
        tools_db = load_json(TOOLS_FILE)
        if tool not in tools_db:
            warn(f"'{tool}' not found. Run  devref --new {tool}  first.")
            return
        if use_notepad:
            template = {"example-topic": {
                "description": "What this topic is about",
                "what_it_does": "Detailed explanation",
                "use_cases": ["When to use this"],
                "syntax": ["command --flag"],
                "examples": ["command --flag value"],
                "tags": []
            }}
            tmp = REF_DIR / f"_add_{tool}_topic.json"
            save_json(tmp, template)
            open_notepad(tmp)
            return
        print(c(f"\n  Adding topic to: {tool.upper()}", "bright"))
        name, data = wizard_topic_entry()
        tools_db[tool].setdefault("topics", {})[name] = data
        save_json(TOOLS_FILE, tools_db)
        success(f"Topic '{name}' added to '{tool}'!")

    elif "--snippets" in args:
        snips_db = load_json(SNIP_FILE)
        if use_notepad:
            template = {"example-pattern": {
                "description": "What this snippet does",
                "use_cases": ["When to use this pattern"],
                "pattern": "command --flag <arg>",
                "examples": ["command --flag value"]
            }}
            tmp = REF_DIR / f"_add_{tool}_snip.json"
            save_json(tmp, template)
            open_notepad(tmp)
            return
        print(c(f"\n  Adding snippet to: {tool.upper()}", "bright"))
        name = smart_input("Snippet name:", hint=HINTS["snip_name"])
        desc = smart_input("Description:", hint=HINTS["snip_desc"])
        ucs  = smart_collect_list("Use cases (one per line)", hint=HINTS["snip_uc"])
        pat  = smart_input("Pattern:", hint=HINTS["snip_pattern"])
        exps = smart_collect_list("Examples (one per line)", hint=HINTS["example_entry"])

        entry = {"description": desc}
        if ucs:  entry["use_cases"] = ucs
        if pat:  entry["pattern"]   = pat
        if exps: entry["examples"]  = exps

        snips_db.setdefault(tool, {}).setdefault("entries", {})[name.lower()] = entry
        save_json(SNIP_FILE, snips_db)
        success(f"Snippet '{name}' added to '{tool}'!")

# ─── Edit command ─────────────────────────────────────────────────────────────
def cmd_edit(args):
    if len(args) < 3:
        warn("Usage: devref --edit <tool> --topic <name>  OR  --edit <tool> --snippets <name>")
        return
    tool = args[0].lower()

    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) else None
        if not topic_name:
            warn("Provide topic name.")
            return
        tools_db = load_json(TOOLS_FILE)
        topics   = tools_db.get(tool, {}).get("topics", {})
        key      = topic_name.lower()
        if key not in topics:
            warn(f"Topic '{key}' not found under '{tool}'.")
            return
        confirm = input(c(f"\n  Type '{key}' to confirm editing: ", "yellow")).strip().lower()
        if confirm != key:
            warn("Cancelled.")
            return

        old = topics[key]
        print(c(f"\n  Editing '{key}'. Press Enter to keep current value.", "cyan"))

        def pk(field, label_text):
            cur = old.get(field, "")
            val = input(c(f"  {label_text} [{cur[:60]}]: ", "yellow")).strip()
            return val if val else cur

        topics[key]["description"]  = pk("description",  "Description")
        topics[key]["what_it_does"] = pk("what_it_does", "What it does")

        repl_uc = input(c("  Replace use cases? (y/n): ", "yellow")).strip().lower()
        if repl_uc == "y":
            topics[key]["use_cases"] = smart_collect_list("New use cases", hint=HINTS["topic_uc"])

        repl_syn = input(c("  Replace syntax? (y/n): ", "yellow")).strip().lower()
        if repl_syn == "y":
            topics[key]["syntax"] = smart_collect_list("New syntax entries", hint=HINTS["syntax_entry"])

        repl_ex = input(c("  Replace examples? (y/n): ", "yellow")).strip().lower()
        if repl_ex == "y":
            topics[key]["examples"] = smart_collect_list("New examples", hint=HINTS["example_entry"])

        save_json(TOOLS_FILE, tools_db)
        success(f"Topic '{key}' updated!")

    elif "--snippets" in args:
        idx = args.index("--snippets")
        snip_name = args[idx + 1] if idx + 1 < len(args) else None
        if not snip_name:
            warn("Provide snippet name.")
            return
        snips_db = load_json(SNIP_FILE)
        entries  = snips_db.get(tool, {}).get("entries", {})
        key      = snip_name.lower()
        if key not in entries:
            warn(f"Snippet '{key}' not found under '{tool}'.")
            return
        confirm = input(c(f"\n  Type '{key}' to confirm editing: ", "yellow")).strip().lower()
        if confirm != key:
            warn("Cancelled.")
            return

        old = entries[key]
        def pk(field, label_text):
            cur = old.get(field, "")
            val = input(c(f"  {label_text} [{cur[:60]}]: ", "yellow")).strip()
            return val if val else cur

        entries[key]["description"] = pk("description", "Description")
        entries[key]["pattern"]     = pk("pattern",     "Pattern")

        repl_uc = input(c("  Replace use cases? (y/n): ", "yellow")).strip().lower()
        if repl_uc == "y":
            entries[key]["use_cases"] = smart_collect_list("New use cases", hint=HINTS["snip_uc"])

        repl_ex = input(c("  Replace examples? (y/n): ", "yellow")).strip().lower()
        if repl_ex == "y":
            entries[key]["examples"] = smart_collect_list("New examples", hint=HINTS["example_entry"])

        save_json(SNIP_FILE, snips_db)
        success(f"Snippet '{key}' updated!")

# ─── Delete command ───────────────────────────────────────────────────────────
def cmd_delete(args):
    if not args:
        warn("Usage: devref --delete <tool>  OR  --delete <tool> --topic <n>  OR  --delete <tool> --snippets <n>")
        return
    tool = args[0].lower()

    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None
        if not topic_name:
            warn("Provide topic name.")
            return
        tools_db = load_json(TOOLS_FILE)
        key = topic_name.lower()
        if key in tools_db.get(tool, {}).get("topics", {}):
            confirm = input(c(f"\n  Type '{key}' to confirm: ", "yellow")).strip().lower()
            if confirm != key:
                warn("Cancelled.")
                return
            del tools_db[tool]["topics"][key]
            save_json(TOOLS_FILE, tools_db)
            success(f"Topic '{key}' deleted.")
        else:
            warn(f"Topic '{key}' not found.")

    elif "--snippets" in args:
        idx = args.index("--snippets")
        snip_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None
        snips_db = load_json(SNIP_FILE)
        tool_snips = snips_db.get(tool, {}).get("entries", {})
        if snip_name:
            key = snip_name.lower()
            if key not in tool_snips:
                warn(f"Snippet '{key}' not found.")
                return
            confirm = input(c(f"\n  Type '{key}' to confirm: ", "yellow")).strip().lower()
            if confirm != key:
                warn("Cancelled.")
                return
            del snips_db[tool]["entries"][key]
            if not snips_db[tool]["entries"]:
                del snips_db[tool]
            save_json(SNIP_FILE, snips_db)
            success(f"Snippet '{key}' deleted.")
        else:
            if tool not in snips_db:
                warn(f"No snippets for '{tool}'.")
                return
            confirm = input(c(f"\n  Type '{tool}' to delete ALL snippets for '{tool}': ", "yellow")).strip().lower()
            if confirm != tool:
                warn("Cancelled.")
                return
            del snips_db[tool]
            save_json(SNIP_FILE, snips_db)
            success(f"All snippets for '{tool}' deleted.")

    else:
        tools_db = load_json(TOOLS_FILE)
        if tool not in tools_db:
            warn(f"'{tool}' not found.")
            return
        confirm = input(c(f"\n  Type '{tool}' to confirm deleting ALL of '{tool}': ", "yellow")).strip().lower()
        if confirm != tool:
            warn("Cancelled.")
            return
        del tools_db[tool]
        save_json(TOOLS_FILE, tools_db)
        success(f"'{tool}' deleted.")

# ─── Tag command ──────────────────────────────────────────────────────────────
def cmd_tag(args):
    if len(args) < 3:
        warn('Usage: devref --tag <tool> <topic> "<tag>"')
        return
    tool, topic, tag = args[0].lower(), args[1].lower(), args[2].strip('"\'')
    tools_db = load_json(TOOLS_FILE)
    topics   = tools_db.get(tool, {}).get("topics", {})
    if topic not in topics:
        warn(f"Topic '{topic}' not found under '{tool}'.")
        return
    topics[topic].setdefault("tags", [])
    if tag not in topics[topic]["tags"]:
        topics[topic]["tags"].append(tag)
    save_json(TOOLS_FILE, tools_db)
    success(f"Tag '{tag}' added to {tool} → {topic}")

def cmd_find_tag(args):
    tag = args[0].strip('"\'') if args else ""
    if not tag:
        warn('Usage: devref --find --tag "<tag>"')
        return
    tools_db = load_json(TOOLS_FILE)
    header(f'Entries tagged: "{tag}"')
    found = False
    for tool, tdata in tools_db.items():
        for tname, topic in tdata.get("topics", {}).items():
            if tag.lower() in [t.lower() for t in topic.get("tags", [])]:
                print(c(f"    {tool}", "yellow") + " → " + c(tname, "green"))
                found = True
    if not found:
        warn(f"No entries with tag '{tag}'.")
    print()

# ─── List command ─────────────────────────────────────────────────────────────
def cmd_list():
    tools_db = load_json(TOOLS_FILE)
    snips_db = load_json(SNIP_FILE)
    if not tools_db and not snips_db:
        warn("No entries yet. Run  devref --new <tool>  to start.")
        return
    header("All Tools in Reference")
    all_tools = sorted(set(list(tools_db.keys()) + list(snips_db.keys())))
    for tool in all_tools:
        t_count = len(tools_db.get(tool, {}).get("topics", {}))
        s_count = len(snips_db.get(tool, {}).get("entries", {}))
        desc    = tools_db.get(tool, {}).get("description", "")
        short   = (desc[:48] + "…") if len(desc) > 48 else desc
        counts  = c(f"[{t_count} topics, {s_count} snippets]", "dim")
        print(c(f"    • {tool}", "green") + f"  {counts}")
        if short:
            print(c(f"        {short}", "dim"))
    print()

# ─── Recent command ───────────────────────────────────────────────────────────
def cmd_recent():
    meta   = load_json(META_FILE)
    recent = meta.get("recent", [])
    if not recent:
        tip("No recent lookups yet.")
        return
    header("Recent Lookups")
    for r in recent[:10]:
        print(c(f"    {r['time']}", "dim") + "  " + c(f"devref {r['query']}", "green"))
    print()

# ─── Backup command ───────────────────────────────────────────────────────────
def cmd_backup():
    import shutil
    ts         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = DEVREF_DIR / "backups" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in [TOOLS_FILE, SNIP_FILE, META_FILE]:
        if f.exists():
            shutil.copy(f, backup_dir / f.name)
    success(f"Backup saved to: {backup_dir}")

# ─── Export command ───────────────────────────────────────────────────────────
def cmd_export(args):
    if not args:
        warn("Usage: devref --export <tool>")
        return
    tool     = args[0].lower()
    tools_db = load_json(TOOLS_FILE)
    snips_db = load_json(SNIP_FILE)
    lines    = [f"# {tool.upper()} Reference\n"]

    tdata = tools_db.get(tool)
    if tdata:
        lines.append(f"**{tdata.get('description','')}**\n")
        if tdata.get("use_cases"):
            lines.append("\n**Use Cases:**\n")
            for uc in tdata["use_cases"]: lines.append(f"- {uc}\n")
        for tname, topic in tdata.get("topics", {}).items():
            lines.append(f"\n## {tname}\n")
            if "description"  in topic: lines.append(f"{topic['description']}\n")
            if "what_it_does" in topic: lines.append(f"\n_{topic['what_it_does']}_\n")
            if topic.get("use_cases"):
                lines.append("\n**Use Cases:**\n")
                for uc in topic["use_cases"]: lines.append(f"- {uc}\n")
            if topic.get("syntax"):
                lines.append("\n**Syntax:**\n")
                for s in topic["syntax"]: lines.append(f"```\n{s}\n```\n")
            if topic.get("examples"):
                lines.append("\n**Examples:**\n")
                for e in topic["examples"]: lines.append(f"```\n{e}\n```\n")

    sdata = snips_db.get(tool, {}).get("entries", {})
    if sdata:
        lines.append("\n## Snippets\n")
        for sname, entry in sdata.items():
            lines.append(f"\n### {sname}\n")
            if "description" in entry: lines.append(f"{entry['description']}\n")
            if entry.get("use_cases"):
                lines.append("\n**Use Cases:**\n")
                for uc in entry["use_cases"]: lines.append(f"- {uc}\n")
            if "pattern" in entry: lines.append(f"\n```\n{entry['pattern']}\n```\n")
            if entry.get("examples"):
                for e in entry["examples"]: lines.append(f"```\n{e}\n```\n")

    out = DEVREF_DIR / f"{tool}_export.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    success(f"Exported to: {out}")

# ─── Import command ───────────────────────────────────────────────────────────
def cmd_import(args):
    if not args:
        warn("Usage: devref --import <file.json>")
        return
    src = Path(args[0])
    if not src.exists():
        warn(f"File not found: {src}")
        return
    new_data = load_json(src)
    tools_db = load_json(TOOLS_FILE)
    merged   = 0
    for key, val in new_data.items():
        if key not in tools_db:
            tools_db[key] = val
            merged += 1
        else:
            for tname, tdata in val.get("topics", {}).items():
                tools_db[key].setdefault("topics", {})[tname] = tdata
                merged += 1
    save_json(TOOLS_FILE, tools_db)
    success(f"Merged {merged} entries from {src.name}")

# ─── Prompt command ───────────────────────────────────────────────────────────
def cmd_prompt(args):
    if not args:
        warn("Usage: devref --prompt <tool>  [--tools | --snippets]")
        return
    tool = args[0]
    mode = "both"
    if "--tools"    in args: mode = "tools"
    if "--snippets" in args: mode = "snippets"

    tools_prompt = f"""
Generate a tools.json entry for devref for the tool: "{tool}"

Use EXACTLY this JSON structure — no extra keys, no markdown fences, raw JSON only:

{{
  "{tool}": {{
    "description": "One-line description of {tool}",
    "tags": ["tag1", "tag2"],
    "use_cases": [
      "When you need to do X",
      "As an alternative to Y when Z"
    ],
    "topics": {{
      "topic-name": {{
        "description": "What this topic is about",
        "what_it_does": "More detailed explanation of behavior",
        "use_cases": [
          "Use this when doing X",
          "Prefer this over Y when Z"
        ],
        "syntax": [
          "command --flag",
          "command --flag <required> [optional]"
        ],
        "examples": [
          "real working example",
          "another concrete example"
        ],
        "tags": ["optional", "topic-level", "tags"]
      }}
    }}
  }}
}}

Requirements:
- Cover at least 6 of the most commonly used topics for "{tool}"
- Make descriptions concise and accurate
- Syntax entries must use <angle-brackets> for required args and [brackets] for optional
- Use cases must be specific and actionable (not generic like "use when needed")
- Output raw JSON only — absolutely no explanation, preamble or markdown fences
"""

    snippets_prompt = f"""
Generate a snippets.json entry for devref for the tool: "{tool}"

Use EXACTLY this JSON structure — no extra keys, no markdown fences, raw JSON only:

{{
  "{tool}": {{
    "entries": {{
      "snippet-name": {{
        "description": "What this snippet/pattern does",
        "use_cases": [
          "Use this when building X",
          "Prefer over Y for Z reasons"
        ],
        "pattern": "command --flag <required> [optional]",
        "examples": [
          "concrete working example here",
          "another real example"
        ]
      }}
    }}
  }}
}}

Requirements:
- Cover at least 6 of the most commonly used patterns/snippets for "{tool}"
- Pattern must be a real command pattern with <required> and [optional] markers
- Use cases must be specific scenarios, not vague descriptions
- Include at least 2 examples per snippet
- Output raw JSON only — no explanation, preamble or markdown fences
"""

    if mode == "tools":
        header(f"AI Prompt  —  {tool.upper()}  →  tools.json")
        print(c(tools_prompt, "white"))
        tip("Paste into Claude or ChatGPT → copy returned JSON → save as file.json")
        tip(f"Then run:  devref --import file.json")

    elif mode == "snippets":
        header(f"AI Prompt  —  {tool.upper()}  →  snippets.json")
        print(c(snippets_prompt, "white"))
        tip("Paste into Claude or ChatGPT → copy returned JSON → save as file.json")
        tip("Note: snippets.json imports need manual merge if file already exists")

    else:
        header(f"AI Prompt  —  {tool.upper()}  →  tools.json")
        print(c(tools_prompt, "white"))
        print()
        print(c("─" * 62, "dim"))
        header(f"AI Prompt  —  {tool.upper()}  →  snippets.json")
        print(c(snippets_prompt, "white"))
        tip("Run each prompt separately  →  save each result as its own .json file")
        tip(f"Then:  devref --import tools_result.json")
        tip(f"And:   devref --import snippets_result.json  (manual merge for snippets)")

# ─── Settings command ─────────────────────────────────────────────────────────
def cmd_set(args):
    if len(args) < 2:
        s = load_settings()
        header("Current Settings")
        for k, v in s.items():
            print(c(f"    {k}", "yellow") + " = " + c(str(v), "green"))
        print()
        return
    key, val = args[0].lower(), args[1].lower()
    settings = load_settings()
    if key == "hints":
        settings["hints"] = (val == "on")
        save_settings(settings)
        state = "ON" if settings["hints"] else "OFF"
        success(f"Hints turned {state}. Wizard prompts will {'show' if settings['hints'] else 'hide'} examples.")
    else:
        warn(f"Unknown setting: '{key}'. Available: hints")

# ─── Entry point ──────────────────────────────────────────────────────────────
def main():
    _migrate_legacy()
    argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        cmd_help()
        return

    cmd  = argv[0].lower()
    rest = argv[1:]

    dispatch = {
        "--find":   lambda: cmd_find_tag(rest[1:]) if rest and rest[0] == "--tag" else cmd_find(rest),
        "--search": lambda: cmd_search(rest),
        "--new":    lambda: cmd_new(rest),
        "--add":    lambda: cmd_add(rest),
        "--edit":   lambda: cmd_edit(rest),
        "--delete": lambda: cmd_delete(rest),
        "--tag":    lambda: cmd_tag(rest),
        "--list":   lambda: cmd_list(),
        "--recent": lambda: cmd_recent(),
        "--backup": lambda: cmd_backup(),
        "--export": lambda: cmd_export(rest),
        "--import": lambda: cmd_import(rest),
        "--prompt": lambda: cmd_prompt(rest),
        "--set":    lambda: cmd_set(rest),
    }

    if cmd in dispatch:
        dispatch[cmd]()
    else:
        warn(f"Unknown command: {cmd}")
        tip("Run  devref --help  for usage")

if __name__ == "__main__":
    main()
