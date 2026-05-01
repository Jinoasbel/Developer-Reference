"""
commands/cmd_find.py - --find command.
"""

from components.display import c, header, warn, tip, display_topic, display_tool_summary
from utils.header import load_header, load_tool_ref, find_tool_keys, resolve_tool
from utils.ids import normalise
from commands.cmd_prompt import cmd_prompt_topic
from commands.cmd_add import cmd_add


def cmd_find(raw_args: list):
    if not raw_args:
        warn("Usage: devref --find <tool>")
        return

    tool_query, rest = resolve_tool(raw_args)
    if not tool_query:
        warn("Usage: devref --find <tool>")
        return

    header_data = load_header()
    matches     = find_tool_keys(tool_query, header_data)

    # ── Multiple matches
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

    tool_key     = matches[0]
    header_entry = header_data[tool_key]
    ref_data     = load_tool_ref(tool_key)

    # --find <tool> --tag <tag>
    if "--tag" in rest:
        idx       = rest.index("--tag")
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
        idx         = rest.index("--prompt")
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
            warn(f"Adding '{topic_name}' as a new topic under '{tool_key}' for prompt generation...")
            cmd_add([tool_key, "--topic", topic_name], inner_call=1)
            # reload ref_data after creation
            ref_data  = load_tool_ref(tool_key)
            topic_data = ref_data.get("topics", {}).get(topic_name, {})
        cmd_prompt_topic(tool_key, topic_name, topic_data, header_entry)
        return

    # --find <tool> --topic <name>
    if "--topic" in rest:
        idx         = rest.index("--topic")
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
