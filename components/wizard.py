"""
components/wizard.py - Interactive terminal wizard helpers (ask, ask_list, collect_topic_data).
"""

from components.display import c, hint_item

HINTS = {
    "tool_desc":     "High-level interpreted programming language",
    "tool_tags":     "language, scripting, data",
    "tool_type":     "interpreter  or  cmdlinetool  or  framework  or  library",
    "topic_name":    "venv  or  listcomprehension  or  pip",
    "topic_desc":    "Virtual environment to isolate project dependencies",
    "topic_type":    "subcommand  or  flag  or  concept  or  workflow",
    "topic_what":    "Creates a self-contained Python environment per project",
    "topic_uc":      "Isolate packages per project  /  Avoid version conflicts",
    "syntax_entry":  "python -m venv <env-name>",
    "example_entry": "python -m venv myenv",
    "flag_entry":    "--verbose >> enables verbose output  |  --output <file> >> write result to file",
    "arg_entry":     "<filename> >> path to input file  |  <port> >> port number to bind  |  [optional] <default>",
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


def ask_flags(label_text: str, hint: str = None) -> dict:
    """
    Collect flag/argument entries in the form  --flag >> description.
    Returns a dict: {"--flag": "description", ...}
    """
    print(c(f"\n  {label_text}", "yellow") +
          c("  (format:  --flag >> description  |  blank to finish)", "dim"))
    if hint:
        hint_item(hint)
    result = {}
    while True:
        val = input(c("    > ", "cyan")).strip()
        if not val:
            break
        if ">>" in val:
            flag, _, desc = val.partition(">>")
            result[flag.strip()] = desc.strip()
        else:
            # accept bare entries without >> as flag with empty desc
            result[val.strip()] = ""
    return result


def collect_tool_type() -> str:
    """Ask for a tool-level type (inner wizard step)."""
    return ask("Tool type (Enter to skip):", hint=HINTS["tool_type"])


def collect_topic_data(inner_call: int = 0) -> dict:
    """
    Collect all fields for a topic interactively.
    When inner_call=1 (auto-created empty topic from cmd_find --prompt),
    all fields are skipped and an empty skeleton is returned immediately.
    """
    if inner_call == 1:
        return {
            "description": "",
            "type":        "",
            "what_it_does":"",
            "use_cases":   [],
            "syntax":      [],
            "examples":    [],
            "flags":       {},
            "arguments":   {},
            "tags":        [],
        }

    desc      = ask("Description:", hint=HINTS["topic_desc"])
    ttype     = ask("Topic type (Enter to skip):", hint=HINTS["topic_type"])
    what      = ask("What it does (Enter to skip):", hint=HINTS["topic_what"])
    ucs       = ask_list("Use cases (one per line)", hint=HINTS["topic_uc"])
    syns      = ask_list("Syntax entries (one per line)", hint=HINTS["syntax_entry"])
    exps      = ask_list("Examples (one per line)", hint=HINTS["example_entry"])
    flags     = ask_flags("Flags  (--flag >> description)", hint=HINTS["flag_entry"])
    arguments = ask_flags("Arguments  (<arg> >> description)", hint=HINTS["arg_entry"])
    tags_raw  = ask("Tags (comma-separated, optional):", hint=HINTS["tool_tags"])
    tags      = [t.strip() for t in tags_raw.split(",") if t.strip()]

    data = {"description": desc}
    if ttype:     data["type"]        = ttype
    if what:      data["what_it_does"]= what
    if ucs:       data["use_cases"]   = ucs
    if syns:      data["syntax"]      = syns
    if exps:      data["examples"]    = exps
    if flags:     data["flags"]       = flags
    if arguments: data["arguments"]   = arguments
    if tags:      data["tags"]        = tags
    return data
