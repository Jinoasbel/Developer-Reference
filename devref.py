"""
devref - Personal Developer Reference CLI
Stores and retrieves your custom help sheets, topics, and syntax references.
"""

import sys
import os
import json
import datetime
import subprocess
import textwrap
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

try:
    from rapidfuzz import fuzz, process
    HAS_FUZZ = True
except ImportError:
    HAS_FUZZ = False

# ─── Paths ────────────────────────────────────────────────────────────────────

DEVREF_DIR = Path(r"S:\devref")
REF_DIR    = DEVREF_DIR / "ref"
REF_FILE   = REF_DIR / "ref.json"
SYN_FILE   = REF_DIR / "syntax.json"
META_FILE  = REF_DIR / "meta.json"   # stores recent history

# ─── Color helpers ────────────────────────────────────────────────────────────

def c(text, color):
    if not HAS_COLOR:
        return text
    colors = {
        "cyan":    Fore.CYAN,
        "green":   Fore.GREEN,
        "yellow":  Fore.YELLOW,
        "magenta": Fore.MAGENTA,
        "white":   Fore.WHITE,
        "bright":  Style.BRIGHT,
        "dim":     Style.DIM,
    }
    return colors.get(color, "") + str(text) + Style.RESET_ALL

def header(text):
    width = 60
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

def dim(text):
    print(c(f"  {text}", "dim"))

def success(text):
    print(c(f"\n  ✔  {text}", "green"))

def warn(text):
    print(c(f"\n  ⚠  {text}", "yellow"))

def tip(text):
    print(c(f"\n  ℹ  {text}", "cyan"))

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

# ─── Recent history ───────────────────────────────────────────────────────────

def record_recent(query: str):
    meta = load_json(META_FILE)
    recent = meta.get("recent", [])
    entry = {"query": query, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    recent = [r for r in recent if r["query"] != query]  # deduplicate
    recent.insert(0, entry)
    meta["recent"] = recent[:20]
    save_json(META_FILE, meta)

# ─── Display helpers ──────────────────────────────────────────────────────────

def display_topic(tool: str, topic: str, data: dict):
    header(f"{tool.upper()}  →  {topic}")
    if "description" in data:
        label("Description")
        item(data["description"])
    if "what_it_does" in data:
        label("What it does")
        item(data["what_it_does"])
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

def display_syntax_entry(tool: str, name: str, data: dict):
    header(f"SYNTAX  {tool.upper()}  →  {name}")
    if "description" in data:
        label("Description")
        item(data["description"])
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
    if "tags" in data and data["tags"]:
        label("Tags")
        item(", ".join(data["tags"]))
    topics = data.get("topics", {})
    if topics:
        label("Topics")
        for t in topics:
            desc = topics[t].get("description", "")
            short = (desc[:60] + "…") if len(desc) > 60 else desc
            print(c(f"    • {t}", "green") + c(f"  —  {short}", "dim"))
    print()
    tip(f"Run:  devref --find {tool} --topic <name>  to view a topic")

# ─── COMMANDS ─────────────────────────────────────────────────────────────────

def cmd_help():
    print(c("""
  ╔══════════════════════════════════════════════════════════╗
  ║              devref  —  Developer Reference CLI          ║
  ╚══════════════════════════════════════════════════════════╝

  FINDING CONTENT
  ───────────────
  devref --find <tool>                   Show tool overview + topics
  devref --find <tool> --topic <name>    Show full topic detail
  devref --find <tool> --syntax          List all syntax entries
  devref --find <tool> --syntax <name>   Show a specific syntax entry

  SEARCHING
  ─────────
  devref --search "<text>"               Search across all entries
  devref --find <tool> --search "<text>" Search within a tool only

  ADDING CONTENT
  ──────────────
  devref --new <tool>                    Add a new tool (wizard)
  devref --new <tool> --notepad          Add a new tool (Notepad template)
  devref --add <tool> --topic            Add a topic to existing tool
  devref --add <tool> --syntax           Add a syntax entry to tool
  devref --add <tool> --topic --notepad  Open topic template in Notepad

  EDITING & DELETING
  ──────────────────
  devref --edit <tool> --topic <name>    Edit a topic (asks confirmation)
  devref --edit <tool> --syntax <name>   Edit a syntax entry
  devref --delete <tool>                 Delete entire tool entry
  devref --delete <tool> --topic <name>  Delete a specific topic

  TAGS
  ────
  devref --tag <tool> <topic> "<tag>"    Tag a topic
  devref --find --tag "<tag>"            Find all entries with a tag

  OTHER
  ─────
  devref --list                          List all tools in reference
  devref --recent                        Show last 10 lookups
  devref --backup                        Backup JSON files
  devref --export <tool>                 Export tool as Markdown
  devref --import <file.json>            Merge external JSON into ref
  devref --prompt <tool>                 Print AI prompt for a tool
  devref --help                          Show this help
""", "white"))

def cmd_find(args):
    tool = args[0].lower() if args else None
    if not tool:
        warn("Usage: devref --find <tool>")
        return

    ref  = load_json(REF_FILE)
    syn  = load_json(SYN_FILE)

    # ── --find python --syntax [name]
    if "--syntax" in args:
        idx = args.index("--syntax")
        syn_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None

        tool_syn = syn.get(tool, {}).get("entries", {})
        if not tool_syn:
            warn(f"No syntax entries found for '{tool}'.")
            return

        if syn_name:
            key = syn_name.lower()
            if key in tool_syn:
                record_recent(f"--find {tool} --syntax {key}")
                display_syntax_entry(tool, key, tool_syn[key])
            else:
                warn(f"Syntax entry '{syn_name}' not found under '{tool}'.")
                tip(f"Run:  devref --find {tool} --syntax  to see all entries")
        else:
            record_recent(f"--find {tool} --syntax")
            header(f"{tool.upper()}  —  Syntax Entries")
            for name, entry in tool_syn.items():
                desc = entry.get("description", "")
                short = (desc[:60] + "…") if len(desc) > 60 else desc
                print(c(f"    • {name}", "green") + c(f"  —  {short}", "dim"))
            print()
            tip(f"Run:  devref --find {tool} --syntax <name>  for details")
        return

    # ── --find python --search "text"
    if "--search" in args:
        idx = args.index("--search")
        query = args[idx + 1] if idx + 1 < len(args) else ""
        query = query.strip('"\'')
        cmd_search([query], scope=tool)
        return

    # ── --find python --topic [name]
    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else None

        tool_data = ref.get(tool)
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

    # ── --find python (plain)
    tool_data = ref.get(tool)
    if not tool_data:
        warn(f"No reference found for '{tool}'.")
        tip("Run:  devref --new " + tool + "  to create one")
        return

    record_recent(f"--find {tool}")
    display_tool_summary(tool, tool_data)

def cmd_search(args, scope=None):
    query = args[0].strip('"\'') if args else ""
    if not query:
        warn("Usage: devref --search \"<text>\"")
        return

    ref = load_json(REF_FILE)
    syn = load_json(SYN_FILE)

    results = []

    tools = [scope] if scope else list(ref.keys()) + list(syn.keys())
    tools = list(dict.fromkeys(tools))  # deduplicate

    for tool in tools:
        # search ref topics
        tool_data = ref.get(tool, {})
        topics = tool_data.get("topics", {})
        for tname, tdata in topics.items():
            blob = " ".join([
                tname,
                tdata.get("description", ""),
                tdata.get("what_it_does", ""),
                " ".join(tdata.get("tags", []))
            ])
            score = fuzz.partial_ratio(query.lower(), blob.lower()) if HAS_FUZZ else (100 if query.lower() in blob.lower() else 0)
            if score >= 60:
                results.append((score, "topic", tool, tname, tdata.get("description", "")))

        # search syntax
        tool_syn = syn.get(tool, {}).get("entries", {})
        for sname, sdata in tool_syn.items():
            blob = " ".join([sname, sdata.get("description", ""), sdata.get("pattern", "")])
            score = fuzz.partial_ratio(query.lower(), blob.lower()) if HAS_FUZZ else (100 if query.lower() in blob.lower() else 0)
            if score >= 60:
                results.append((score, "syntax", tool, sname, sdata.get("description", "")))

    if not results:
        warn(f"No results found for '{query}'.")
        return

    results.sort(key=lambda x: x[0], reverse=True)
    header(f"Search results for: \"{query}\"" + (f"  [in: {scope}]" if scope else ""))
    for score, kind, tool, name, desc in results:
        short = (desc[:55] + "…") if len(desc) > 55 else desc
        kind_label = c(f"[{kind}]", "cyan")
        tool_label = c(tool, "yellow")
        name_label = c(name, "green")
        score_label = c(f"{score}%", "dim")
        print(f"    {tool_label} → {name_label}  {kind_label}  {score_label}")
        if short:
            print(c(f"        {short}", "dim"))
    print()
    tip("Run  devref --find <tool> --topic <name>  to view full entry")

def wizard_collect_list(prompt_label: str) -> list:
    """Prompt user to enter multiple items, blank line to finish."""
    items = []
    print(c(f"\n  {prompt_label}  (blank line to finish)", "yellow"))
    while True:
        val = input(c("    > ", "cyan")).strip()
        if not val:
            break
        items.append(val)
    return items

def wizard_topic(tool: str) -> tuple[str, dict]:
    """Run interactive wizard for a single topic. Returns (name, data)."""
    print(c("\n  ── Topic Wizard ──", "cyan"))
    name = input(c("  Topic name: ", "yellow")).strip().lower()
    description = input(c("  Description: ", "yellow")).strip()
    what_it_does = input(c("  What it does (optional, Enter to skip): ", "yellow")).strip()
    syntax_list = wizard_collect_list("Syntax entries (one per line)")
    examples_list = wizard_collect_list("Examples (one per line)")
    tags_raw = input(c("\n  Tags (comma-separated, optional): ", "yellow")).strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    data = {"description": description}
    if what_it_does:
        data["what_it_does"] = what_it_does
    if syntax_list:
        data["syntax"] = syntax_list
    if examples_list:
        data["examples"] = examples_list
    if tags:
        data["tags"] = tags

    return name, data

def open_notepad_template(path: Path):
    subprocess.Popen(["notepad.exe", str(path)])
    tip(f"Opened in Notepad: {path}")
    tip("Save and close when done. Run devref --import to load it back if needed.")

def cmd_new(args):
    if not args:
        warn("Usage: devref --new <tool>")
        return

    tool = args[0].lower()
    use_notepad = "--notepad" in args

    ref = load_json(REF_FILE)

    if tool in ref:
        warn(f"'{tool}' already exists. Use  devref --add {tool} --topic  to add topics.")
        return

    if use_notepad:
        template = {
            tool: {
                "description": "Describe this tool here",
                "tags": ["tag1", "tag2"],
                "topics": {
                    "example-topic": {
                        "description": "What this topic is about",
                        "what_it_does": "Detailed explanation",
                        "syntax": ["command --flag"],
                        "examples": ["command --flag value"],
                        "tags": []
                    }
                }
            }
        }
        tmp = REF_DIR / f"_new_{tool}.json"
        save_json(tmp, template)
        open_notepad_template(tmp)
        tip(f"After editing, run:  devref --import S:\\devref\\ref\\_new_{tool}.json")
        return

    print(c(f"\n  Creating new reference: {tool.upper()}", "bright"))
    description = input(c("  Tool description: ", "yellow")).strip()
    tags_raw = input(c("  Tags (comma-separated, optional): ", "yellow")).strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    topics = {}
    print(c("\n  Now add topics (Enter blank topic name to finish):", "cyan"))
    while True:
        name_check = input(c("\n  Topic name (blank to finish): ", "yellow")).strip().lower()
        if not name_check:
            break
        # Reuse wizard but name already collected
        tdesc = input(c("  Description: ", "yellow")).strip()
        twhat = input(c("  What it does (optional): ", "yellow")).strip()
        tsyn  = wizard_collect_list("Syntax")
        texmp = wizard_collect_list("Examples")
        ttags_raw = input(c("\n  Tags (comma-separated, optional): ", "yellow")).strip()
        ttags = [t.strip() for t in ttags_raw.split(",") if t.strip()]

        tdata = {"description": tdesc}
        if twhat:   tdata["what_it_does"] = twhat
        if tsyn:    tdata["syntax"]       = tsyn
        if texmp:   tdata["examples"]     = texmp
        if ttags:   tdata["tags"]         = ttags
        topics[name_check] = tdata

    entry = {"description": description}
    if tags:    entry["tags"]   = tags
    if topics:  entry["topics"] = topics

    ref[tool] = entry
    save_json(REF_FILE, ref)
    success(f"'{tool}' added to reference!")
    tip(f"Run:  devref --find {tool}  to view it")

def cmd_add(args):
    if len(args) < 2:
        warn("Usage: devref --add <tool> --topic  OR  devref --add <tool> --syntax")
        return

    tool = args[0].lower()
    use_notepad = "--notepad" in args

    if "--topic" in args:
        ref = load_json(REF_FILE)
        if tool not in ref:
            warn(f"'{tool}' not found. Run  devref --new {tool}  first.")
            return

        if use_notepad:
            template = {
                "example-topic": {
                    "description": "What this topic is about",
                    "what_it_does": "Detailed explanation",
                    "syntax": ["command --flag"],
                    "examples": ["command --flag value"],
                    "tags": []
                }
            }
            tmp = REF_DIR / f"_add_{tool}_topic.json"
            save_json(tmp, template)
            open_notepad_template(tmp)
            return

        print(c(f"\n  Adding topic to: {tool.upper()}", "bright"))
        name, data = wizard_topic(tool)
        ref[tool].setdefault("topics", {})[name] = data
        save_json(REF_FILE, ref)
        success(f"Topic '{name}' added to '{tool}'!")

    elif "--syntax" in args:
        syn = load_json(SYN_FILE)
        if use_notepad:
            template = {
                "example-pattern": {
                    "description": "What this syntax does",
                    "pattern": "command --flag <arg>",
                    "examples": ["command --flag value"]
                }
            }
            tmp = REF_DIR / f"_add_{tool}_syntax.json"
            save_json(tmp, template)
            open_notepad_template(tmp)
            return

        print(c(f"\n  Adding syntax to: {tool.upper()}", "bright"))
        print(c("\n  ── Syntax Wizard ──", "cyan"))
        name = input(c("  Syntax name: ", "yellow")).strip().lower()
        desc = input(c("  Description: ", "yellow")).strip()
        pattern = input(c("  Pattern (e.g. git commit -m \"<msg>\"): ", "yellow")).strip()
        examples = wizard_collect_list("Examples")

        entry = {"description": desc, "pattern": pattern}
        if examples: entry["examples"] = examples

        syn.setdefault(tool, {}).setdefault("entries", {})[name] = entry
        save_json(SYN_FILE, syn)
        success(f"Syntax '{name}' added to '{tool}'!")

def cmd_edit(args):
    if len(args) < 3:
        warn("Usage: devref --edit <tool> --topic <name>  OR  --edit <tool> --syntax <name>")
        return

    tool = args[0].lower()

    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) else None
        if not topic_name:
            warn("Provide topic name: devref --edit <tool> --topic <name>")
            return

        ref = load_json(REF_FILE)
        topics = ref.get(tool, {}).get("topics", {})
        key = topic_name.lower()
        if key not in topics:
            warn(f"Topic '{key}' not found under '{tool}'.")
            return

        confirm = input(c(f"\n  Type '{key}' to confirm editing: ", "yellow")).strip().lower()
        if confirm != key:
            warn("Confirmation did not match. Edit cancelled.")
            return

        print(c(f"\n  Editing '{key}' under '{tool}'. Press Enter to keep current value.", "cyan"))
        old = topics[key]

        def prompt_keep(field, label_text):
            cur = old.get(field, "")
            val = input(c(f"  {label_text} [{cur}]: ", "yellow")).strip()
            return val if val else cur

        topics[key]["description"]  = prompt_keep("description", "Description")
        topics[key]["what_it_does"] = prompt_keep("what_it_does", "What it does")

        replace_syn = input(c("  Replace syntax list? (y/n): ", "yellow")).strip().lower()
        if replace_syn == "y":
            topics[key]["syntax"] = wizard_collect_list("New syntax entries")

        replace_ex = input(c("  Replace examples? (y/n): ", "yellow")).strip().lower()
        if replace_ex == "y":
            topics[key]["examples"] = wizard_collect_list("New examples")

        save_json(REF_FILE, ref)
        success(f"Topic '{key}' updated!")

    elif "--syntax" in args:
        idx = args.index("--syntax")
        syn_name = args[idx + 1] if idx + 1 < len(args) else None
        if not syn_name:
            warn("Provide syntax name: devref --edit <tool> --syntax <name>")
            return

        syn = load_json(SYN_FILE)
        entries = syn.get(tool, {}).get("entries", {})
        key = syn_name.lower()
        if key not in entries:
            warn(f"Syntax '{key}' not found under '{tool}'.")
            return

        confirm = input(c(f"\n  Type '{key}' to confirm editing: ", "yellow")).strip().lower()
        if confirm != key:
            warn("Confirmation did not match. Edit cancelled.")
            return

        old = entries[key]
        def prompt_keep(field, label_text):
            cur = old.get(field, "")
            val = input(c(f"  {label_text} [{cur}]: ", "yellow")).strip()
            return val if val else cur

        entries[key]["description"] = prompt_keep("description", "Description")
        entries[key]["pattern"]     = prompt_keep("pattern", "Pattern")

        replace_ex = input(c("  Replace examples? (y/n): ", "yellow")).strip().lower()
        if replace_ex == "y":
            entries[key]["examples"] = wizard_collect_list("New examples")

        save_json(SYN_FILE, syn)
        success(f"Syntax '{key}' updated!")

def cmd_delete(args):
    if not args:
        warn("Usage: devref --delete <tool>  OR  devref --delete <tool> --topic <name>")
        return

    tool = args[0].lower()

    if "--topic" in args:
        idx = args.index("--topic")
        topic_name = args[idx + 1] if idx + 1 < len(args) else None
        if not topic_name:
            warn("Provide topic name.")
            return
        ref = load_json(REF_FILE)
        key = topic_name.lower()
        if key in ref.get(tool, {}).get("topics", {}):
            confirm = input(c(f"\n  Type '{key}' to confirm deletion: ", "yellow")).strip().lower()
            if confirm != key:
                warn("Cancelled.")
                return
            del ref[tool]["topics"][key]
            save_json(REF_FILE, ref)
            success(f"Topic '{key}' deleted from '{tool}'.")
        else:
            warn(f"Topic '{key}' not found.")
    else:
        ref = load_json(REF_FILE)
        if tool not in ref:
            warn(f"'{tool}' not found.")
            return
        confirm = input(c(f"\n  Type '{tool}' to confirm deleting ALL of '{tool}': ", "yellow")).strip().lower()
        if confirm != tool:
            warn("Cancelled.")
            return
        del ref[tool]
        save_json(REF_FILE, ref)
        success(f"'{tool}' deleted from reference.")

def cmd_tag(args):
    if len(args) < 3:
        warn("Usage: devref --tag <tool> <topic> \"<tag>\"")
        return
    tool, topic, tag = args[0].lower(), args[1].lower(), args[2].strip('"\'')
    ref = load_json(REF_FILE)
    topics = ref.get(tool, {}).get("topics", {})
    if topic not in topics:
        warn(f"Topic '{topic}' not found under '{tool}'.")
        return
    topics[topic].setdefault("tags", [])
    if tag not in topics[topic]["tags"]:
        topics[topic]["tags"].append(tag)
    save_json(REF_FILE, ref)
    success(f"Tag '{tag}' added to {tool} → {topic}")

def cmd_find_tag(args):
    tag = args[0].strip('"\'') if args else ""
    if not tag:
        warn("Usage: devref --find --tag \"<tag>\"")
        return
    ref = load_json(REF_FILE)
    header(f"Entries tagged: \"{tag}\"")
    found = False
    for tool, tdata in ref.items():
        for tname, topic in tdata.get("topics", {}).items():
            if tag.lower() in [t.lower() for t in topic.get("tags", [])]:
                print(c(f"    {tool}", "yellow") + " → " + c(tname, "green"))
                found = True
    if not found:
        warn(f"No entries found with tag '{tag}'.")
    print()

def cmd_list():
    ref = load_json(REF_FILE)
    syn = load_json(SYN_FILE)
    if not ref and not syn:
        warn("No entries yet. Run  devref --new <tool>  to get started.")
        return
    header("All Tools in Reference")
    all_tools = sorted(set(list(ref.keys()) + list(syn.keys())))
    for tool in all_tools:
        t_count = len(ref.get(tool, {}).get("topics", {}))
        s_count = len(syn.get(tool, {}).get("entries", {}))
        desc = ref.get(tool, {}).get("description", "")
        short = (desc[:50] + "…") if len(desc) > 50 else desc
        counts = c(f"[{t_count} topics, {s_count} syntax]", "dim")
        print(c(f"    • {tool}", "green") + f"  {counts}")
        if short:
            print(c(f"        {short}", "dim"))
    print()

def cmd_recent():
    meta = load_json(META_FILE)
    recent = meta.get("recent", [])
    if not recent:
        tip("No recent lookups yet.")
        return
    header("Recent Lookups")
    for r in recent[:10]:
        print(c(f"    {r['time']}", "dim") + "  " + c(f"devref {r['query']}", "green"))
    print()

def cmd_backup():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = DEVREF_DIR / "backups" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in [REF_FILE, SYN_FILE, META_FILE]:
        if f.exists():
            import shutil
            shutil.copy(f, backup_dir / f.name)
    success(f"Backup saved to: {backup_dir}")

def cmd_export(args):
    if not args:
        warn("Usage: devref --export <tool>")
        return
    tool = args[0].lower()
    ref = load_json(REF_FILE)
    syn = load_json(SYN_FILE)

    lines = [f"# {tool.upper()} Reference\n"]

    tdata = ref.get(tool)
    if tdata:
        lines.append(f"**{tdata.get('description', '')}**\n")
        for tname, topic in tdata.get("topics", {}).items():
            lines.append(f"\n## {tname}\n")
            if "description"  in topic: lines.append(f"{topic['description']}\n")
            if "what_it_does" in topic: lines.append(f"\n_{topic['what_it_does']}_\n")
            if topic.get("syntax"):
                lines.append("\n**Syntax:**\n")
                for s in topic["syntax"]: lines.append(f"```\n{s}\n```\n")
            if topic.get("examples"):
                lines.append("\n**Examples:**\n")
                for e in topic["examples"]: lines.append(f"```\n{e}\n```\n")

    sdata = syn.get(tool, {}).get("entries", {})
    if sdata:
        lines.append("\n## Syntax Reference\n")
        for sname, entry in sdata.items():
            lines.append(f"\n### {sname}\n")
            if "description" in entry: lines.append(f"{entry['description']}\n")
            if "pattern"     in entry: lines.append(f"\n```\n{entry['pattern']}\n```\n")
            if entry.get("examples"):
                for e in entry["examples"]: lines.append(f"```\n{e}\n```\n")

    out = DEVREF_DIR / f"{tool}_export.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    success(f"Exported to: {out}")

def cmd_import(args):
    if not args:
        warn("Usage: devref --import <file.json>")
        return
    src = Path(args[0])
    if not src.exists():
        warn(f"File not found: {src}")
        return
    new_data = load_json(src)
    ref = load_json(REF_FILE)
    merged = 0
    for key, val in new_data.items():
        if key not in ref:
            ref[key] = val
            merged += 1
        else:
            # merge topics
            for tname, tdata in val.get("topics", {}).items():
                ref[key].setdefault("topics", {})[tname] = tdata
                merged += 1
    save_json(REF_FILE, ref)
    success(f"Merged {merged} entries from {src.name}")

def cmd_prompt(args):
    if not args:
        warn("Usage: devref --prompt <tool>")
        return
    tool = args[0]
    prompt = f"""
You are helping me build a devref entry for "{tool}".

devref is a personal CLI reference tool. Generate a JSON block that follows this exact structure:

For ref.json (topics/help entries):
{{
  "{tool}": {{
    "description": "One-line description of {tool}",
    "tags": ["relevant", "tags"],
    "topics": {{
      "topic-name": {{
        "description": "What this topic is about",
        "what_it_does": "More detailed explanation",
        "syntax": [
          "command --flag",
          "command --flag <arg>"
        ],
        "examples": [
          "real example command here",
          "another example"
        ],
        "tags": ["optional", "tags"]
      }}
    }}
  }}
}}

For syntax.json (shorthand syntax cards):
{{
  "{tool}": {{
    "entries": {{
      "syntax-name": {{
        "description": "What this syntax does",
        "pattern": "command --flag <required> [optional]",
        "examples": [
          "real example"
        ]
      }}
    }}
  }}
}}

Please generate BOTH blocks for "{tool}" covering the most commonly used commands, topics, and syntax patterns.
Cover at least 5 topics and 5 syntax entries.
Output raw JSON only — no explanation, no markdown fences.
"""
    header(f"AI Prompt for: {tool.upper()}")
    print(c(prompt, "white"))
    tip("Copy the above prompt → paste into Claude or ChatGPT → copy the JSON output")
    tip(f"Save as a .json file → run:  devref --import <file.json>  to load it")

# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        cmd_help()
        return

    cmd = argv[0].lower()
    rest = argv[1:]

    if cmd == "--find":
        if len(rest) >= 2 and rest[0] == "--tag":
            cmd_find_tag(rest[1:])
        else:
            cmd_find(rest)
    elif cmd == "--search":
        cmd_search(rest)
    elif cmd == "--new":
        cmd_new(rest)
    elif cmd == "--add":
        cmd_add(rest)
    elif cmd == "--edit":
        cmd_edit(rest)
    elif cmd == "--delete":
        cmd_delete(rest)
    elif cmd == "--tag":
        cmd_tag(rest)
    elif cmd == "--list":
        cmd_list()
    elif cmd == "--recent":
        cmd_recent()
    elif cmd == "--backup":
        cmd_backup()
    elif cmd == "--export":
        cmd_export(rest)
    elif cmd == "--import":
        cmd_import(rest)
    elif cmd == "--prompt":
        cmd_prompt(rest)
    else:
        warn(f"Unknown command: {cmd}")
        tip("Run  devref --help  for usage")

if __name__ == "__main__":
    main()
