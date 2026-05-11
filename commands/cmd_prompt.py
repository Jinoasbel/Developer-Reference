"""
commands/cmd_prompt.py - --prompt command (generate AI prompt for a tool or topic).
"""

import json

from components.display import c, header, warn, tip
from utils.header import load_header, load_tool_ref, find_tool_keys, resolve_tool


def cmd_prompt(raw_args: list):
    if not raw_args:
        warn("Usage: devref --prompt <tool>")
        return

    tool_query, _ = resolve_tool(raw_args)
    tool          = tool_query

    header_data  = load_header()
    matches      = find_tool_keys(tool, header_data)
    tool_display = matches[0] if matches else tool

    prompt_text = f"""
Generate a tool reference entry for devref for the tool: "{tool_display}"

Use EXACTLY this JSON structure — raw JSON only, no markdown fences, no preamble:

{{
  "id": "AUTO",
  "name": "{tool_display}",
  "type": "interpreter | cmdlinetool | framework | library | builtin | packagemanager",
  "topics": {{
    "topicname": {{
      "name": "topicname",
      "type": "subcommand | flag | concept | workflow",
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
      ],
      "flags": {{
        "--verbose": "enables verbose output",
        "--output <file>": "write result to file"
      }},
      "arguments": {{
        "<filename>": "path to input file",
        "<port>": "port number to bind"
      }}
    }}
  }}
}}

Requirements:
- Set "type" at the tool level to the most accurate category (e.g. interpreter, cmdlinetool, framework, library)
- Cover most commonly used topics for "{tool_display}"
- Each topic should have a "type" field (subcommand, flag, concept, or workflow)
- Descriptions: concise and accurate
- Syntax: use <angle-brackets> for required args and [brackets] for optional
- Use cases: specific and actionable
- flags: only include if the topic has real flags/options; use "--flag" or "--flag <arg>" as keys
- arguments: only include if the topic takes positional args; use "<argname>" as keys
- Multiple topics may be included in this single file — add as many topic blocks as needed
- Output raw JSON only — no explanation, preamble or markdown fences
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
    "type": "subcommand | flag | concept | workflow",
    "tags": ["tag1"],
    "description": "...",
    "what_it_does": "...",
    "use_cases": ["..."],
    "syntax": ["command --flag <required>"],
    "examples": ["example here"],
    "flags": {{
      "--verbose": "enables verbose output",
      "--output <file>": "write result to file"
    }},
    "arguments": {{
      "<filename>": "path to input file"
    }}
  }},
  "optionalextratopic": {{ ... }}
}}

Notes:
- "type" should be one of: subcommand, flag, concept, workflow
- flags: key is the flag string (e.g. "--no-cache"), value is its description
- arguments: key is the positional arg (e.g. "<path>"), value is its description
- Omit "flags" or "arguments" if not applicable to this topic
"""
    print(c(prompt_text, "white"))
    tip(f"Paste into AI → save result → run:  devref --import result.json --tool {tool_key}")
