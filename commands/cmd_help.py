"""
commands/cmd_help.py - --help command.
"""

from components.display import c, section_header, BOX, _center


def cmd_help():
    print()
    print(c("  ╔" + "═" * BOX + "╗", "cyan"))
    print(c("  ║", "cyan") + c(_center("devref  —  Developer Reference CLI"), "bright") + c("║", "cyan"))
    print(c("  ║", "cyan") + c(_center("v 2.1"), "dim")                                  + c("║", "cyan"))
    print(c("  ╚" + "═" * BOX + "╝", "cyan"))

    section_header("FINDING TOOLS & TOPICS", "yellow")
    rows = [
        ("devref --find <tool>",                 "Tool overview + all topics"),
        ("devref --find <tool> --topic <name>",  "Full detail on a topic"),
        ("devref --find <tool> --id <ID>",       "Find redundant Tool with ID")
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("SEARCHING", "magenta")
    rows = [
        ("devref --search <tag>",                 "Search tags across ALL tool entries"),
        ("devref --find <tool> --tag <tag>",       "Search tags within one tool"),
    ]
    for cmd_str, desc in rows:
        print(c(f"    {cmd_str:<46}", "green") + c(desc, "dim"))

    section_header("ADDING CONTENT", "cyan")
    rows = [
        ("devref --new <tool>",                   "New tool wizard (terminal)"),
        ("devref --new <tool> --notepad",          "New tool in console editor"),
        ("devref --add <tool> --topic <name>",     "Add topic via terminal wizard"),
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
        ("devref --export <tool>",                "Export tool as single JSON file"),
        ("devref --import <file>",                "Import a Json Tool file"),
        ("devref --import <file> --tool <name> --topic", "import file as topic under tool"),
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
