"""
commands/cmd_search.py - --search command (tag-based cross-tool search).
"""

from components.display import c, header, warn
from utils.header import load_header, load_tool_ref
from utils.ids import normalise


def cmd_search(raw_args: list):
    """devref --search <tag>  — search tags across all tools."""
    tag_parts = [a for a in raw_args if not a.startswith("--")]
    tag       = normalise(" ".join(tag_parts))
    if not tag:
        warn('Usage: devref --search <tag>')
        return

    header_data = load_header()
    header(f'Tag search: "{tag}"')
    found = False

    for tool_key in header_data.get("tools", []):
        ref_data   = load_tool_ref(tool_key)
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
                print(c(f"    {tool_key}", "yellow") + " → " +
                      c(tname, "green") + c("  [topic tag]", "dim"))
                found = True

    if not found:
        warn(f"No entries tagged '{tag}'.")
    print()
