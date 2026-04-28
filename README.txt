==========================================================
  devref v3.0  --  Developer Reference CLI
  README  --  Complete Working Guide
==========================================================


----------------------------------------------------------
  WHAT IS DEVREF?
----------------------------------------------------------

devref is a personal, offline developer reference tool that
runs entirely in your terminal. It lets you store, search,
and retrieve structured help sheets for any CLI tool, language,
framework, or concept you use regularly.

Everything is stored in plain JSON files that you own and
control. No cloud, no accounts, no internet required.


----------------------------------------------------------
  DIRECTORY STRUCTURE
----------------------------------------------------------

  devref/
  ├── devref.py           Main CLI script
  ├── devref.bat          Windows launcher
  ├── src/
  │   └── header.json     Master index of all tools
  ├── ref/
  │   ├── git.json        One file per tool
  │   ├── python.json
  │   └── ...
  └── notes/
      ├── ideas.txt       Personal notes (timestamped)
      └── ...

src/header.json  is the master index. It lists all registered
tools, their IDs, tags, descriptions and topic names.

ref/<tool>.json  holds the actual topic data for each tool.
One file per tool — separate from the index for fast lookup.

notes/  holds plain text notes created with  devref --note.


----------------------------------------------------------
  header.json STRUCTURE
----------------------------------------------------------

{
  "tools": ["git", "python", "docker"],

  "git": {
    "id": "A3F9C1",
    "name": "git",
    "tags": ["vcs", "version-control"],
    "description": "Distributed version control system",
    "topics": ["commit", "branch", "rebase"]
  },

  "python": {
    ...
  }
}

  tools      Ordered list of all registered tool keys
  id         6-digit uppercase hexadecimal, auto-generated
             IDs are case-insensitive (A3F9C1 == a3f9c1)
  name       Display name (may differ from key)
  tags       Tool-level tags, used by --search
  description  One-line summary
  topics     List of topic names stored in the ref file


----------------------------------------------------------
  ref/<tool>.json STRUCTURE
----------------------------------------------------------

{
  "id": "A3F9C1",
  "name": "git",
  "topics": {
    "commit": {
      "name": "commit",
      "tags": ["basics", "workflow"],
      "description": "Record changes to the repository",
      "what_it_does": "Creates a snapshot of staged changes",
      "use_cases": [
        "Save progress after completing a feature",
        "Create a checkpoint before risky changes"
      ],
      "syntax": [
        "git commit -m \"<message>\"",
        "git commit --amend"
      ],
      "examples": [
        "git commit -m \"fix: correct off-by-one in loop\"",
        "git commit --amend --no-edit"
      ]
    }
  }
}


----------------------------------------------------------
  TOOL NAME MATCHING
----------------------------------------------------------

Tool names are matched case-insensitively and
separator-insensitively. This means:

  devref --find git
  devref --find Git
  devref --find G_it
  devref --find g-it
  devref --find GIT

...all find the same tool.

Multi-word tool names are joined automatically:

  devref --find hello world
  → looks up the tool "helloworld"

  devref --add hello world --topic setup
  → adds a topic to the tool "helloworld"

This applies to every command that takes a tool name.
You never need quotes around tool names or topic names.


----------------------------------------------------------
  ID DISPLAY
----------------------------------------------------------

When two tools have names that are identical after
normalisation (e.g. "git" and "Git" were added separately),
devref shows both with their hex IDs and lets you select
one by ID:

  devref --find git --id A3F9C1


----------------------------------------------------------
  COMPLETE COMMAND REFERENCE
----------------------------------------------------------

FINDING CONTENT ─────────────────────────────────────────

  devref --find <tool>
      Show tool overview: ID, description, tags, topic list.

  devref --find <tool> --topic <name>
      Show full detail for one topic: description, what it
      does, use cases, syntax, examples, tags.

  devref --find <tool> --tag <tag>
      List all topics under that tool that carry the given tag.

  devref --find <tool> --prompt <topic>
      Generate an AI prompt to improve or fill in that topic.
      The prompt hints that multiple topics can be returned
      in a single file.


SEARCHING ───────────────────────────────────────────────

  devref --search <tag>
      Search tags across ALL tools and ALL topics.
      Returns tool-level and topic-level matches.

  devref --find <tool> --tag <tag>
      Same as above but scoped to one tool's topics only.

  Note: search is tag-based only. Free-text word search
  across descriptions has been removed in v3.0.


ADDING CONTENT ──────────────────────────────────────────

  devref --new <tool>
      Launch the terminal wizard to create a new tool.
      Asks for description, tags, and any number of topics.
      Input is collected field-by-field.

  devref --new <tool> --notepad
      Open a JSON template in your console editor (nano/vim
      on Linux/Mac, notepad.exe on Windows). Edit and save
      to create the tool. The template follows the exact
      ref/<tool>.json structure.

  devref --add <tool> --topic <name>
      Add a topic to an existing tool via the terminal wizard.
      Asks for description, what it does, use cases, syntax,
      examples and tags.

  devref --add <tool> --topic <name> --notepad
      Open a JSON template for the new topic in the console
      editor. You can include multiple topic blocks in the
      file — all will be added.


EDITING ─────────────────────────────────────────────────

  devref --edit <tool>
      Edit the tool's name, description and tags in the
      console editor. Current values are pre-loaded so you
      only change what you need. Topic data is not touched.

  devref --edit <tool> --topic <name>
      Open the full topic JSON in the console editor with
      all current data pre-loaded. Edit any field, save and
      close. Changes are applied immediately.

  The console editor is your system's default ($EDITOR).
  If $EDITOR is not set, devref tries nano, then vim, then
  notepad.exe. You always see the current content and can
  make surgical edits without retyping everything.


DELETING ────────────────────────────────────────────────

  devref --del <tool>
      Delete the entire tool: removes its header entry and
      its ref/<tool>.json file. Requires typing the tool
      name to confirm.

  devref --del <tool> --topic <name>
      Delete one topic from a tool. Requires typing the
      topic name to confirm.


AI PROMPT ───────────────────────────────────────────────

  devref --prompt <tool>
      Print an AI prompt you can paste into Claude or
      ChatGPT to generate a complete tool reference entry.
      The prompt asks for multiple topics in a single JSON
      file matching the ref/<tool>.json structure.

  devref --find <tool> --prompt <topic>
      Print an AI prompt to improve or fill in a specific
      topic. The prompt includes the current topic data and
      hints that additional related topics may be included
      in the returned file.

  Workflow:
    1. Run devref --prompt <tool>
    2. Copy the prompt
    3. Paste into Claude (claude.ai) or ChatGPT
    4. Copy the returned JSON
    5. Save as a .json file
    6. Run: devref --import myfile.json --tool <tool>


IMPORT / EXPORT ─────────────────────────────────────────

  devref --export <tool>
      Export a tool as a single self-contained JSON file
      named <tool>_export.json in the devref directory.
      This file can be re-imported on another machine.

  devref --import <file>
      Import a file that was previously exported with
      --export. Auto-detects the tool name from the file.
      If the tool already exists, topics are merged in.

  devref --import <file> --tool <name>
      Import the file as a new tool with the given name.
      If the tool already exists, topics are merged.

  devref --import <file> --tool <name> --topic <file2>
      Create a new tool from <file>, then also add topic(s)
      from <file2>. <file2> may contain one or many topics.
      If <file2> has a "topics" wrapper key the contents are
      extracted; otherwise the root keys are treated as
      topic names directly.


NOTES ───────────────────────────────────────────────────

  devref --note
      List all saved notes with last-modified timestamps.

  devref --note <name>
      Open or create a note named <name> in the console
      editor. On first creation a header comment is added
      automatically. When you save and close, a timestamp
      line is appended:
        # Last saved: 2025-04-28 14:32:07

  devref --note <name> --del
      Delete the note after typing the name to confirm.

  Notes are stored as plain .txt files in notes/ and are
  fully editable outside devref at any time.


UTILS ───────────────────────────────────────────────────

  devref --list
      List all registered tools with their hex IDs,
      descriptions and topic counts.

  devref --help
      Show the full command reference in the terminal.

  devref  (no arguments)
      Same as --help.


----------------------------------------------------------
  CONSOLE EDITOR BEHAVIOUR
----------------------------------------------------------

devref opens the console editor for:
  --new <tool> --notepad
  --add <tool> --topic <name> --notepad
  --edit <tool>
  --edit <tool> --topic <name>
  --note <name>

Editor selection order:
  1. $EDITOR environment variable (if set)
  2. nano   (Linux / Mac)
  3. vim    (Linux / Mac fallback)
  4. notepad.exe  (Windows)

To force a specific editor:
  Windows:  set EDITOR=notepad
  Linux:    export EDITOR=nano


----------------------------------------------------------
  TAGS
----------------------------------------------------------

Tags exist at two levels:

  Tool-level tags   stored in header.json under the tool
  Topic-level tags  stored in the topic's "tags" array

To search all tags across everything:
  devref --search <tag>

To search tags within one tool's topics:
  devref --find <tool> --tag <tag>

Tags are matched after normalisation (case and separator
insensitive), so "Version-Control" matches "versioncontrol".


----------------------------------------------------------
  MULTI-WORD NAMES
----------------------------------------------------------

All multi-word arguments before the first -- flag are joined
into a single normalised string. This means:

  devref --find hello world --topic quick start
  → finds tool "helloworld", topic "quickstart"

  devref --del my tool --topic some feature
  → deletes topic "somefeature" from tool "mytool"

You never need quotes.


----------------------------------------------------------
  TIPS
----------------------------------------------------------

- Use --prompt to bulk-generate entries via AI rather than
  typing everything manually.

- After generating JSON with AI, always glance at it before
  importing to catch hallucinated syntax.

- The --edit commands pre-load current data in the editor
  so you can fix a single typo without retyping everything.

- devref --note is useful for scratchpad ideas that are not
  yet structured enough to be a full tool entry.

- JSON files in ref/ are plain text. You can edit them
  directly in any editor — just keep valid JSON format.
  Run  devref --list  afterward to verify all tools load.

- To rename a tool: export it, delete it, re-import with
  --tool <new-name>.

==========================================================
