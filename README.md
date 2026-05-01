# devref

A personal, offline developer reference CLI. Store, search, and retrieve
structured help sheets for any CLI tool, language, framework, or concept
you use regularly — all local JSON, no cloud, no accounts, no internet
required. No dependencies beyond `colorama`.

---

## Table of Contents

- [Project Layout](#project-layout)
- [Data Architecture](#data-architecture)
  - [Header Index](#header-index-srcheaderjson)
  - [Tool Reference Files](#tool-reference-files-reftoolkeyjson)
  - [Topic Schema](#topic-schema)
  - [Notes](#notes-notes)
- [Module Map](#module-map)
- [Command Reference](#command-reference)
  - [Finding & Viewing](#finding--viewing)
  - [Searching by Tag](#searching-by-tag)
  - [Adding Content](#adding-content)
  - [Editing](#editing)
  - [Deleting](#deleting)
  - [AI Prompt Generation](#ai-prompt-generation)
  - [Import / Export](#import--export)
  - [Notes](#notes-1)
  - [Utils](#utils)
- [Key Design Patterns](#key-design-patterns)
- [Name Matching & IDs](#name-matching--ids)
- [Tags](#tags)
- [Console Editor Behaviour](#console-editor-behaviour)
- [Tips](#tips)
- [Extending devref](#extending-devref)

---

## Project Layout

```
devref/
│
├── devref.py               # Entry point — arg dispatch table
├── devref.bat              # Windows launcher
│
├── commands/               # One file per CLI command
│   ├── cmd_find.py
│   ├── cmd_search.py
│   ├── cmd_new.py
│   ├── cmd_add.py
│   ├── cmd_edit.py
│   ├── cmd_del.py
│   ├── cmd_list.py
│   ├── cmd_export.py
│   ├── cmd_import.py
│   ├── cmd_prompt.py
│   └── cmd_note.py
│
├── components/             # Shared UI and input helpers
│   ├── display.py          # Color printing, section headers, topic/tool display
│   ├── editor.py           # Opens vim/nano/notepad for in-terminal editing
│   └── wizard.py           # Interactive ask/ask_list/ask_flags collectors
│
├── utils/                  # Data layer
│   ├── fs.py               # Path constants, load_json / save_json
│   ├── header.py           # Header CRUD, tool-ref file helpers, resolve_tool
│   └── ids.py              # generate_hex_id, normalise, fuzzy_name_match
│
├── src/
│   └── header.json         # Master index of all tools (auto-created)
│
├── ref/
│   └── <toolkey>.json      # One file per tool (auto-created)
│
└── notes/
    └── <name>.txt          # Free-text notes (auto-created)
```

---

## Data Architecture

devref splits storage into two tiers so the master index stays small and
fast, while full topic data is only loaded on demand.

### Header Index (`src/header.json`)

The header is the single source of truth for tool existence and discovery.
It contains lightweight metadata for every registered tool.

```json
{
  "tools": ["git", "python", "docker"],

  "git": {
    "id":          "A3F9C1",
    "name":        "git",
    "type":        "cmdlinetool",
    "description": "Distributed version control system",
    "tags":        ["vcs", "versioning"],
    "topics":      ["commit", "rebase", "stash"]
  },

  "python": { ... }
}
```

`"tools"` is an ordered list of all tool keys. Each tool key maps to its
own metadata object. The `"topics"` array lists topic keys present in that
tool's ref file — it is kept in sync on every write.

**`type` field (tool level)** — describes the category of the tool:

| Value            | Meaning                                       |
|------------------|-----------------------------------------------|
| `interpreter`    | Runtime that executes code (Python, Node)     |
| `cmdlinetool`    | Standalone CLI binary (git, curl, jq)         |
| `framework`      | Application framework (Django, React)         |
| `library`        | Importable code library                       |
| `builtin`        | Shell built-in or OS primitive                |
| `packagemanager` | Package/dependency manager (pip, npm)         |

### Tool Reference Files (`ref/<toolkey>.json`)

Each tool gets its own file. Topics are stored here in full.

```json
{
  "id":     "A3F9C1",
  "name":   "git",
  "topics": {
    "commit": { ... },
    "rebase": { ... }
  }
}
```

The file is only loaded when a command explicitly needs topic data
(`--find`, `--edit`, `--add`, etc.). List and search commands use the
header only.

### Topic Schema

Every topic object lives inside `"topics"` keyed by its normalised name.

```json
"commit": {
  "name":         "commit",
  "type":         "subcommand",
  "tags":         ["history", "snapshot"],
  "description":  "Record staged changes as a new commit",
  "what_it_does": "Writes the index to the object store and advances HEAD",
  "use_cases": [
    "Save a logical unit of work with a message",
    "Create a checkpoint before a risky refactor"
  ],
  "syntax": [
    "git commit -m <message>",
    "git commit --amend [--no-edit]"
  ],
  "examples": [
    "git commit -m \"fix: null check in auth handler\"",
    "git commit --amend --no-edit"
  ],
  "flags": {
    "--amend":      "rewrite the previous commit",
    "--no-edit":    "keep the existing commit message",
    "-m <message>": "set commit message inline"
  },
  "arguments": {
    "<message>": "the commit message string"
  }
}
```

**`type` field (topic level)** — describes the nature of the topic:

| Value        | Meaning                                          |
|--------------|--------------------------------------------------|
| `subcommand` | A named subcommand (`git commit`, `docker run`)  |
| `flag`       | A specific flag or option (`--verbose`)          |
| `concept`    | A mental model or idea (branching strategy)      |
| `workflow`   | A multi-step process (release flow)              |

**`flags`** — a `{ "--flag": "description" }` map. Keys use the actual
flag string including any arg placeholder, e.g. `"--output <file>"`. Omit
if the topic has no flags.

**`arguments`** — a `{ "<argname>": "description" }` map for positional
arguments. Keys use angle-bracket notation. Omit if the topic takes no
positional args.

### Notes (`notes/`)

Plain `.txt` files managed by `cmd_note`. No schema — freeform text. Each
file is named by its normalised note name and auto-timestamped on save.

---

## Module Map

### `devref.py` — Entry Point

Parses `sys.argv`, maps the first flag to a command function via a dispatch
dict, passes the remaining args as a raw list. No logic lives here.

```python
dispatch = {
    "--find":   lambda: cmd_find(rest),
    "--new":    lambda: cmd_new(rest),
    ...
}
```

### `utils/fs.py` — Filesystem Layer

Defines path constants and the two primitives everything else builds on:

- `load_json(path)` — returns `{}` if the file doesn't exist
- `save_json(path, data)` — creates parent dirs, writes with `indent=2`

Path roots (`DEVREF_DIR`, `SRC_DIR`, `REF_DIR`, `NOTES_DIR`) are resolved
relative to the script location, or to `sys.executable` when frozen.

### `utils/ids.py` — Identity and Normalisation

- `generate_hex_id()` — random 6-digit uppercase hex, used as a stable ID
- `normalise(name)` — strips spaces, hyphens, underscores, lowercases. All
  internal key comparisons go through this: `"Git"`, `"g-it"`, `"g_it"`
  all resolve to `"git"`
- `fuzzy_name_match(query, candidate)` — thin wrapper:
  `normalise(q) == normalise(c)`

### `utils/header.py` — Header and Ref CRUD

The data access layer:

| Function | Purpose |
|---|---|
| `load_header()` | Load `header.json`, ensure `"tools"` key exists |
| `save_header(data)` | Write header back |
| `load_tool_ref(tool_key)` | Load `ref/<toolkey>.json` |
| `save_tool_ref(tool_key, data)` | Write ref file |
| `find_tool_keys(query, header_data)` | Return all keys matching a query via `fuzzy_name_match` |
| `add_tool_to_header(...)` | Create a new header entry, return its hex ID |
| `resolve_tool(raw_args)` | Split `["git", "--topic", "commit"]` → `("git", ["--topic", "commit"])` |

`resolve_tool` joins all leading non-flag tokens into one tool name, so
`devref --find my tool --topic foo` works even with multi-word tool names.

### `components/display.py` — Output Layer

All terminal output goes through here. Color is applied via `colorama` if
installed, otherwise text passes through unchanged.

Key display functions:

- `display_topic(tool, topic, data)` — renders all fields of a topic in
  order, including `flags` and `arguments` as key→description tables
- `display_tool_summary(tool_key, header_entry, ref_data)` — overview with
  topic list
- `section_header`, `header`, `label`, `item`, `syntax_item`,
  `example_item`, `usecase_item` — consistent visual hierarchy

### `components/wizard.py` — Interactive Input

Used by `--new` and `--add` for the terminal wizard flow.

- `ask(prompt, hint)` — single-line input with a dim hint shown above
- `ask_list(label, hint)` — multi-line input, blank line to finish
- `ask_flags(label, hint)` — collects `--flag >> description` pairs,
  returns `{"--flag": "description"}` dict
- `collect_topic_data(inner_call=0)` — orchestrates all topic fields. When
  `inner_call=1` it writes an empty skeleton without prompting (used by the
  `--prompt` command to silently pre-create a topic)
- `collect_tool_type()` — prompts for a tool-level type string

### `components/editor.py` — In-Terminal Editor

- `open_console_editor(initial_content)` — writes content to a temp file,
  opens it in `$EDITOR` → `nano` → `vim` → `vi` (or `notepad.exe` on
  Windows), returns the saved text
- `open_console_editor_json(initial_dict)` — serialises a dict to JSON,
  runs it through the editor, parses and returns the result

---

## Command Reference

### Finding & Viewing

```
devref --find <tool>
```
Show tool overview: ID, type, description, tags, topic list.

```
devref --find <tool> --topic <name>
```
Show full detail for one topic: description, type, what_it_does, use_cases,
tags, syntax, examples, flags, arguments.

```
devref --find <tool> --tag <tag>
```
List all topics under that tool that carry the given tag.

```
devref --find <tool> --prompt <topic>
```
Generate an AI prompt to improve or fill in that topic. If the topic does
not yet exist it is auto-created as an empty skeleton first. The prompt
hints that multiple topics can be returned in a single file.

---

### Searching by Tag

```
devref --search <tag>
```
Search tags across **all** tools and **all** topics. Returns tool-level
and topic-level matches.

```
devref --find <tool> --tag <tag>
```
Same as above but scoped to one tool's topics only.

Note: search is tag-based only. Free-text word search was removed in v3.0.

---

### Adding Content

#### New tool — terminal wizard

```
devref --new <tool>
```
Prompts for description, type, and tags. Calls `add_tool_to_header` to
write the header entry, then enters a loop prompting for topics. Saves
header and ref on exit.

#### New tool — editor

```
devref --new <tool> --notepad
```
Opens a JSON template (including `type`, `flags`, `arguments` placeholders)
in your console editor. On save, parses and imports the result directly.

#### Add topic — terminal wizard

```
devref --add <tool> --topic <name>
```
Calls `collect_topic_data()` interactively, writes the result into the
tool's ref file, and appends the topic key to the header's `"topics"` list.

#### Add topic — editor

```
devref --add <tool> --topic <name> --notepad
```
Opens a single-topic JSON template in your editor. You can include multiple
topic blocks in the file — all will be added.

---

### Editing

```
devref --edit <tool>
```
Opens an editor with `name`, `description`, and `tags` pre-loaded. Edit
only what needs changing, save and close to apply. Topic data is not
touched.

```
devref --edit <tool> --topic <name>
```
Opens the full topic JSON in the console editor with all current data
pre-loaded. Edit any field, save and close. Changes are applied
immediately.

The console editor is your system's default (`$EDITOR`). If `$EDITOR` is
not set, devref tries `nano`, then `vim`, then `notepad.exe`.

---

### Deleting

```
devref --del <tool>
```
Delete the entire tool: removes its header entry and its
`ref/<toolkey>.json` file. Requires typing the tool name to confirm.

```
devref --del <tool> --topic <name>
```
Delete one topic from a tool. Requires typing the topic name to confirm.

---

### AI Prompt Generation

```
devref --prompt <tool>
```
Prints a structured prompt you can paste into Claude or ChatGPT to
generate a complete tool reference entry. The prompt requests a full tool
JSON file including `type` at the tool level and `type`, `flags`, and
`arguments` inside each topic. Multiple topics can be included in one file.
The result can be imported directly with `--import`.

```
devref --find <tool> --prompt <topic>
```
Prints a prompt scoped to one topic, seeded with the current topic data so
the AI can improve it. If the topic does not exist it is auto-created as an
empty skeleton first (via `cmd_add` with `inner_call=1`). Also hints that
additional related topics may be included in the response.

**Workflow:**

```
1. Run  devref --prompt <tool>
2. Copy the prompt
3. Paste into Claude (claude.ai) or ChatGPT
4. Copy the returned JSON
5. Save as a .json file
6. Run: devref --import myfile.json --tool <tool>
```

---

### Import / Export

#### Export

```
devref --export <tool>
```
Writes a single self-contained JSON file `<toolkey>_export.json` containing
`id`, `name`, `description`, `type`, `tags`, and all `topics`. This format
is identical to what the AI prompt commands produce and can be re-imported
on another machine.

#### Import

```
devref --import <file>
```
Auto-detects a tool export (has a top-level `"topics"` key). Infers the
tool name from `"name"` in the file or the filename stem. If the tool
already exists, topics are merged in.

```
devref --import <file> --tool <name>
```
Explicitly name the tool. Same merge behaviour if it already exists.

```
devref --import <file> --tool <name> --topic
```
Reads `<file>` as a topic map and adds its entries as topics under the
named tool. The file should be either a plain topic map:

```json
{
  "topicname":    { "name": "...", "description": "...", ... },
  "anothertopic": { ... }
}
```

or a full tool export (the function skips `id`, `name`, `description`,
`tags`, and `type` keys automatically).

Import is idempotent — re-importing an updated export merges topics rather
than overwriting.

---

### Notes

```
devref --note
```
List all saved notes with last-modified timestamps.

```
devref --note <name>
```
Open or create a note named `<name>` in the console editor. On first
creation a header comment is added automatically. When you save and close,
a timestamp line is appended:
```
# Last saved: 2025-04-28 14:32:07
```

```
devref --note <name> --del
```
Delete the note after typing the name to confirm.

Notes are stored as plain `.txt` files in `notes/` and are fully editable
outside devref at any time.

---

### Utils

```
devref --list
```
List all registered tools with their hex IDs, type, descriptions and topic
counts.

```
devref --help
```
Show the full command reference in the terminal.

```
devref  (no arguments)
```
Same as `--help`.

---

## Key Design Patterns

**Two-tier storage** — The header is always loaded; ref files are loaded
only when a command needs topics. This keeps list and search fast
regardless of how much topic data is stored.

**Normalised keys everywhere** — All tool names and topic names pass
through `normalise()` before being used as dict keys or compared. This
means `"Git"`, `"g-it"`, `"GIT"` all resolve to the same entry.
User-facing display uses the stored `"name"` field.

**`inner_call` flag** — `cmd_add` accepts `inner_call=1` which bypasses
the interactive wizard and writes an empty skeleton. This is used by
`cmd_find --prompt` to silently pre-create a topic before generating the
AI prompt, so the prompt is always seeded with *something*.

**`resolve_tool`** — All commands that take a tool name call
`resolve_tool(raw_args)` first. It splits the arg list at the first `--`
flag, joins the leading tokens into a tool name string, and returns
`(tool_name, remaining_flags)`. This means tool names can contain spaces
or multiple words without needing quotes.

**Editor flow** — `--notepad` variants always pre-fill a complete JSON
template so the user has structure to edit rather than a blank file.
`open_console_editor` respects `$EDITOR` and falls back through
`nano → vim → vi → notepad`.

**Import is idempotent** — If a tool key already exists during import,
`_import_as_new_tool` merges topics rather than overwriting, so
re-importing an updated export is safe.

---

## Name Matching & IDs

Tool and topic names are matched **case-insensitively** and
**separator-insensitively**. All of the following find the same tool:

```
devref --find git
devref --find Git
devref --find G_it
devref --find g-it
devref --find GIT
```

Multi-word tool names are joined automatically — you never need quotes:

```
devref --find hello world          → looks up "helloworld"
devref --add hello world --topic setup
```

When two tools have names that are identical after normalisation, devref
shows both with their hex IDs and lets you select one:

```
devref --find git --id A3F9C1
```

Every tool has a 6-digit uppercase hexadecimal ID auto-generated at
creation time. IDs are case-insensitive (`A3F9C1 == a3f9c1`) and are used
for disambiguation only; normal lookup is always by name.

---

## Tags

Tags exist at two levels:

- **Tool-level tags** — stored in `header.json` under the tool
- **Topic-level tags** — stored in the topic's `"tags"` array

```
devref --search <tag>              # search all tools and all topics
devref --find <tool> --tag <tag>   # search topics within one tool
```

Tags are matched after normalisation (case and separator insensitive), so
`"Version-Control"` matches `"versioncontrol"`.

---

## Console Editor Behaviour

devref opens the console editor for:

- `--new <tool> --notepad`
- `--add <tool> --topic <name> --notepad`
- `--edit <tool>`
- `--edit <tool> --topic <name>`
- `--note <name>`

Editor selection order:

1. `$EDITOR` environment variable (if set)
2. `nano` (Linux / Mac)
3. `vim` (Linux / Mac fallback)
4. `vi` (Linux / Mac fallback)
5. `notepad.exe` (Windows)

To force a specific editor:

```
Windows:  set EDITOR=notepad
Linux:    export EDITOR=nano
```

---

## Tips

- Use `--prompt` to bulk-generate entries via AI rather than typing
  everything manually.
- After generating JSON with AI, always glance at it before importing to
  catch hallucinated syntax.
- The `--edit` commands pre-load current data so you can fix a single typo
  without retyping everything.
- `devref --note` is useful for scratchpad ideas not yet structured enough
  to be a full tool entry.
- JSON files in `ref/` are plain text — you can edit them directly in any
  editor. Keep valid JSON format and run `devref --list` afterward to
  verify all tools load.
- To rename a tool: export it, delete it, re-import with `--tool <new-name>`.

---

## Extending devref

**Adding a new command:**

1. Create `commands/cmd_mycommand.py` with a `cmd_mycommand(raw_args: list)` function.
2. Import it in `devref.py`.
3. Add `"--mycommand": lambda: cmd_mycommand(rest)` to the dispatch dict.
4. Add a help row in `cmd_help.py`.

**Adding a new topic field:**

1. Add it to the `collect_topic_data()` return dict in `wizard.py`.
2. Add display logic in `display_topic()` in `display.py`.
3. Update the JSON template in `cmd_new.py` (notepad path).
4. Update the AI prompt templates in `cmd_prompt.py`.

**Changing the data directory:**

Edit the path constants in `utils/fs.py`. `DEVREF_DIR` is the root; all
other paths derive from it.
