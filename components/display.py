"""
components/display.py - Color helpers, print utilities, and content display functions.
"""

import textwrap

# ─── Optional deps ────────────────────────────────────────────────────────────
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

BOX = 60

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

def _center(text):
    pad = BOX - len(text)
    return " " * (pad // 2) + text + " " * (pad - pad // 2)

# ─── Print utilities ──────────────────────────────────────────────────────────
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

# ─── Content display ──────────────────────────────────────────────────────────
def display_topic(tool: str, topic: str, data: dict):
    header(f"{tool.upper()}  →  {topic}")
    if data.get("type"):
        label("Type")
        item(data["type"])
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
    if "flags" in data and data["flags"]:
        label("Flags")
        for flag, desc in data["flags"].items():
            print(c(f"    {flag}", "green") + c(f"  >>  {desc}", "dim"))
    if "arguments" in data and data["arguments"]:
        label("Arguments")
        for arg, desc in data["arguments"].items():
            print(c(f"    {arg}", "magenta") + c(f"  >>  {desc}", "dim"))
    print()

def display_tool_summary(tool_key: str, header_entry: dict, ref_data: dict):
    header(f"{header_entry.get('name', tool_key).upper()}  —  Overview")
    label("ID")
    item(header_entry.get("id", "N/A"))
    if header_entry.get("type"):
        label("Type")
        item(header_entry["type"])
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
            desc  = tdata.get("description", "")
            short = (desc[:55] + "…") if len(desc) > 55 else desc
            print(c(f"    • {t}", "green") + c(f"  —  {short}", "dim"))
    print()
    tip(f"Run:  devref --find {tool_key} --topic <name>  to view a topic")
