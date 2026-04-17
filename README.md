# devref — Personal Developer Reference CLI

A fast, colorful command-line tool for storing and retrieving your own
developer notes — commands, syntax patterns, use cases, and examples —
organized by tool and topic, searchable by keyword or fuzzy text.

---

## What it does

devref is a personal knowledge base that lives in your terminal. Instead
of Googling the same git command or conda syntax for the hundredth time,
you add it once and retrieve it in seconds. Everything is stored in two
plain JSON files you own completely.

---

## Two files, two purposes

**tools.json** — Structured reference entries.
Each tool (python, git, conda, docker…) has a description, tags, use cases,
and topics. Each topic has description, what it does, use cases, syntax
patterns, and examples.

**snippets.json** — Quick pattern cards.
Short reusable patterns: f-strings, lambda expressions, git stash, rebase.
Each snippet has a pattern template with `<required>` and `[optional]`
markers, plus concrete examples.

---

## Installation (Windows)

1. Run `build_windows.bat` on a machine with Python installed.
   This installs PyInstaller + dependencies and compiles `devref.exe`.
2. Run `devref-setup.exe` (built from the NSIS script) **or**
   run `install.bat` to copy files to your S: drive manually.
3. Add the install directory to your system PATH (install.bat shows instructions).
4. Open a new terminal and type `devref --help`.

### Dependencies (auto-installed by build script)
- `colorama` — color output (optional, degrades gracefully)
- `rapidfuzz` — fuzzy search (optional, falls back to substring match)
- `prompt_toolkit` — autocomplete in wizards (optional, can be toggled)

---

## Commands

### Finding content

```
devref --find <tool>                     Tool overview + all topics
devref --find <tool> --topic <name>      Full detail on a specific topic
devref --find <tool> --snippets          List all snippets for a tool
devref --find <tool> --snippets <name>   Show one snippet in full
devref --find --tag <tag>                Find all entries with a tag
```

### Searching

```
devref --search "text"                         Search everything
devref --search "text" --tools                 Search tools.json only
devref --search "text" --snippets              Search snippets.json only
devref --find <tool> --search "text"           Search within one tool
devref --find <tool> --search "text" --topics      Topics only
devref --find <tool> --search "text" --snippets    Snippets only
devref --find <tool> --search "text" --usecases    Use cases only
devref --find <tool> --search "text" --examples    Examples only
```

Results are ranked by fuzzy score and labeled by type (topic, snippet,
usecase, example) with color coding.

### Adding content

```
devref --new <tool>                    Interactive wizard — new tool entry
devref --new <tool> --notepad          Opens JSON template in Notepad instead
devref --add <tool> --topic            Add a topic to an existing tool
devref --add <tool> --snippets         Add a snippet to an existing tool
devref --add <tool> --topic --notepad  Topic template in Notepad
```

### Editing and deleting

```
devref --edit <tool> --topic <name>      Edit a topic (type name to confirm)
devref --edit <tool> --snippets <name>   Edit a snippet
devref --delete <tool>                   Delete entire tool entry
devref --delete <tool> --topic <name>    Delete one topic
devref --delete <tool> --snippets <name> Delete one snippet
```

### Tags

```
devref --tag <tool> <topic> "<tag>"   Add a tag to a topic
devref --find --tag "<tag>"           Find all entries with that tag
```

### AI-assisted entry generation

devref can generate the exact prompt to paste into an AI chat to produce
correctly structured JSON for either file.

```
devref --prompt <tool>              Prompt for both files
devref --prompt <tool> --tools      Prompt for tools.json only
devref --prompt <tool> --snippets   Prompt for snippets.json only
```

Paste the output into Claude or ChatGPT → copy the returned JSON → save
as a .json file → import it:

```
devref --import result.json
```

The importer automatically detects whether the file is a tools or snippets
JSON and writes to the correct file.

### Settings and utilities

```
devref --set hints on/off         Toggle example hints in wizard prompts
devref --set autocomplete on/off  Toggle prompt_toolkit autocomplete
devref --set                      Show current settings
devref --list                     List all tools with topic/snippet counts
devref --recent                   Show last 10 lookups
devref --backup                   Backup JSON files with timestamp
devref --export <tool>            Export a tool as a Markdown file
devref --import <file>            Merge JSON into tools or snippets
devref --help                     Show help
```

---

## Data storage

All data is stored in plain JSON files inside the `ref\` subdirectory of
wherever devref is installed. You can back them up, sync them to a USB
drive, or version-control them with git. The `--backup` command creates
timestamped copies inside a `backups\` folder.

File migration from v1.x is automatic: if the old `ref.json` and
`syntax.json` names are found and the new names are absent, they are
renamed on first run.

---

## Settings

| Setting      | Default | Description                                      |
|--------------|---------|--------------------------------------------------|
| hints        | on      | Show grey example hints above each wizard prompt |
| autocomplete | on      | Use prompt_toolkit for tab-complete in wizards   |

Toggle with `devref --set <name> on/off`.
If prompt_toolkit is not installed, autocomplete silently falls back to
plain input regardless of the setting.

---

## Project files

| File                | Purpose                                      |
|---------------------|----------------------------------------------|
| devref.py           | Main program source                          |
| devref.exe          | Compiled executable (from build_windows.bat) |
| devref.bat          | Thin wrapper so `devref` works on PATH       |
| devref-setup.nsi    | NSIS installer script                        |
| install.bat         | Manual install to S: drive                   |
| build_windows.bat   | Compiles devref.exe with PyInstaller         |
| ref\tools.json      | Your tools/topics reference data             |
| ref\snippets.json   | Your pattern/snippet data                    |
| ref\meta.json       | Settings and recent-lookup history           |
| devref_guide.txt    | Quick-reference guide (shown in installer)   |
