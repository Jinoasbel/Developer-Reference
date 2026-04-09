# devref — Personal Developer Reference CLI

A portable, offline CLI tool that acts as your personal cheat sheet for any tool, language, or workflow. Store, search, and retrieve help topics and syntax patterns from the terminal.

## Overview

`devref` manages two types of content stored in JSON files:

| File | Purpose |
|------|---------|
| `ref.json` | **Topics** — detailed help entries with descriptions, syntax, examples, and tags |
| `syntax.json` | **Syntax cards** — quick-reference patterns with descriptions and examples |

Both files live in a `ref/` subdirectory next to the executable.

## Architecture

```
devref/                     ← Install directory (auto-detected)
├── devref.exe              ← Compiled CLI binary (PyInstaller)
├── devref.py               ← Source code (885 lines Python)
├── devref.bat              ← Fallback: runs via python directly
├── devref_guide.txt        ← User guide + AI prompt template
├── ref/
│   ├── ref.json            ← Topic entries (per-tool)
│   ├── syntax.json         ← Syntax card entries (per-tool)
│   └── meta.json           ← Auto-managed recent lookup history
├── backups/                ← Timestamped backups (created by --backup)
├── installer.nsi           ← NSIS installer script
└── build_windows.bat       ← Build script (compiles .exe)
```

### Path Resolution

The application auto-detects its location at runtime:
- **As compiled exe** (`PyInstaller`): uses the directory containing `devref.exe`
- **As Python script**: uses the directory containing `devref.py`

This means the tool works regardless of where it's installed — no hardcoded paths.

### Dependencies

| Package | Purpose | Required? |
|---------|---------|-----------|
| `colorama` | Color-coded terminal output | Optional (graceful fallback) |
| `rapidfuzz` | Fuzzy string matching for `--search` | Optional (falls back to substring match) |

Both are bundled into the exe during PyInstaller compilation.

## JSON Schemas

### ref.json

```json
{
  "tool-name": {
    "description": "One-line description of the tool",
    "tags": ["tag1", "tag2"],
    "topics": {
      "topic-name": {
        "description": "What this topic is about",
        "what_it_does": "Detailed explanation",
        "syntax": ["command --flag <arg>"],
        "examples": ["command --flag value"],
        "tags": ["optional", "tags"]
      }
    }
  }
}
```

### syntax.json

```json
{
  "tool-name": {
    "entries": {
      "syntax-name": {
        "description": "What this syntax pattern does",
        "pattern": "command --flag <required> [optional]",
        "examples": ["real example"]
      }
    }
  }
}
```

### meta.json (auto-managed)

```json
{
  "recent": [
    { "query": "--find python --topic venv", "time": "2026-04-09 19:30" }
  ]
}
```

## Command Reference

### Finding Content

| Command | Description |
|---------|-------------|
| `devref --find <tool>` | Show tool overview + list of topics |
| `devref --find <tool> --topic <name>` | Show full detail for a specific topic |
| `devref --find <tool> --syntax` | List all syntax entries for a tool |
| `devref --find <tool> --syntax <name>` | Show a specific syntax entry |

### Searching

| Command | Description |
|---------|-------------|
| `devref --search "<text>"` | Fuzzy search across all entries (ref + syntax) |
| `devref --find <tool> --search "<text>"` | Search within a specific tool only |

Search uses `rapidfuzz.partial_ratio` with a 60% threshold. Falls back to substring matching if `rapidfuzz` is not installed.

### Adding Content

| Command | Description |
|---------|-------------|
| `devref --new <tool>` | Interactive wizard to create a new tool entry |
| `devref --new <tool> --notepad` | Create a JSON template and open in Notepad |
| `devref --add <tool> --topic` | Add a topic to an existing tool (wizard) |
| `devref --add <tool> --topic --notepad` | Open topic template in Notepad |
| `devref --add <tool> --syntax` | Add a syntax entry to a tool (wizard) |

### Editing Content

| Command | Description |
|---------|-------------|
| `devref --edit <tool> --topic <name>` | Edit a topic (type topic name to confirm) |
| `devref --edit <tool> --syntax <name>` | Edit a syntax entry (type name to confirm) |

Editing prompts for each field with the current value shown in brackets. Press Enter to keep the current value.

### Deleting Content

| Command | Description |
|---------|-------------|
| `devref --delete <tool>` | Delete entire tool from ref.json |
| `devref --delete <tool> --topic <name>` | Delete a specific topic |
| `devref --delete <tool> --syntax <name>` | Delete a specific syntax entry |
| `devref --delete <tool> --syntax` | Delete all syntax entries for a tool |

All delete operations require typing the name to confirm (safety measure).

### Tags

| Command | Description |
|---------|-------------|
| `devref --tag <tool> <topic> "<tag>"` | Add a tag to a topic |
| `devref --find --tag "<tag>"` | Find all entries with a specific tag |

### Utilities

| Command | Description |
|---------|-------------|
| `devref --list` | List all tools with topic/syntax counts |
| `devref --recent` | Show last 10 lookups |
| `devref --backup` | Create timestamped backup of all JSON files |
| `devref --export <tool>` | Export a tool as a Markdown file |
| `devref --import <file.json>` | Merge external JSON into ref.json |
| `devref --prompt <tool>` | Print an AI prompt template for bulk-generating entries |
| `devref --help` | Show full command reference |

## Installation

### Option A: NSIS Installer (Recommended)

1. **Build the exe** first (requires Python + pip):
   ```
   build_windows.bat
   ```

2. **Compile the installer** (requires NSIS):
   ```
   S:\NSIS\makensis.exe installer.nsi
   ```

3. **Run** `devref-setup.exe`:
   - Choose your install directory
   - PATH is automatically configured
   - Open a **new** terminal and run `devref --help`

4. **Uninstall** via Add/Remove Programs → "devref", or run `uninstall.exe` from the install directory.

### Option B: Manual Install

1. Build the exe:
   ```
   build_windows.bat
   ```

2. Run the install script:
   ```
   install.bat
   ```
   This copies files to `S:\devref\` and provides manual PATH setup instructions.

### Option C: Run Without Compiling

Place `devref.bat` and `devref.py` in a directory on your PATH. Requires Python to be installed.

## Development Guide

### Source Structure

The entire application is a single Python file (`devref.py`, ~890 lines) organized into these sections:

| Section | Lines | Description |
|---------|-------|-------------|
| Imports & Dependencies | 1–25 | Optional colorama + rapidfuzz with graceful fallbacks |
| Path Configuration | 27–40 | Auto-detection of install directory |
| Color Helpers | 42–84 | Terminal formatting functions (`c()`, `header()`, `label()`, etc.) |
| JSON Helpers | 88–97 | `load_json()` / `save_json()` with auto-directory creation |
| Recent History | 101–108 | Deduplicating recent lookup tracker |
| Display Helpers | 112–163 | Rendering functions for topics, syntax entries, tool summaries |
| Commands | 167–840 | All `cmd_*()` functions implementing CLI features |
| Entry Point | 845–895 | Argument parser routing to command functions |

### Key Functions

| Function | Purpose |
|----------|---------|
| `cmd_find(args)` | Routes `--find` with `--topic`, `--syntax`, `--search` sub-flags |
| `cmd_search(args, scope)` | Fuzzy search across ref + syntax, optional tool scope |
| `cmd_new(args)` | Interactive wizard or Notepad template for new tools |
| `cmd_add(args)` | Add topics or syntax entries to existing tools |
| `cmd_edit(args)` | Edit topics or syntax entries with confirmation |
| `cmd_delete(args)` | Delete tools, topics, or syntax entries with confirmation |
| `wizard_topic(tool)` | Interactive topic entry collection |
| `wizard_collect_list(prompt)` | Multi-line input collection (blank line to finish) |

### Adding a New Command

1. Create a `cmd_yourcommand(args)` function
2. Add routing in `main()` (line ~850): `elif cmd == "--yourcommand": cmd_yourcommand(rest)`
3. Add help text in `cmd_help()`

### Building

```bash
# Install dependencies
pip install pyinstaller colorama rapidfuzz

# Compile to single exe
pyinstaller --onefile --name devref --distpath . devref.py

# Clean up build artifacts
rmdir /s /q build
del devref.spec
```

Or simply run `build_windows.bat`.

### Building the Installer

Requires [NSIS](https://nsis.sourceforge.io/) installed:

```bash
S:\NSIS\makensis.exe installer.nsi
```

Produces `devref-setup.exe` in the project directory.

## AI Prompt Workflow

The `--prompt` command generates a pre-filled prompt for any tool. The workflow:

1. `devref --prompt conda` — prints the AI prompt
2. Paste into Claude/ChatGPT
3. AI returns JSON blocks for both `ref.json` and `syntax.json`
4. Save as `conda.json`
5. `devref --import conda.json` — merges into your reference

See `devref_guide.txt` for the full prompt template.

## License

MIT