"""
devref v2.1 - Personal Developer Reference CLI
"""

import sys

from commands.cmd_help   import cmd_help
from commands.cmd_find   import cmd_find
from commands.cmd_search import cmd_search
from commands.cmd_new    import cmd_new
from commands.cmd_add    import cmd_add
from commands.cmd_edit   import cmd_edit
from commands.cmd_del    import cmd_del
from commands.cmd_list   import cmd_list
from commands.cmd_export import cmd_export
from commands.cmd_import import cmd_import
from commands.cmd_prompt import cmd_prompt
from commands.cmd_note   import cmd_note
from components.display  import warn, tip


def main():
    argv = sys.argv[1:]

    if not argv or argv[0] in ("--help", "-h"):
        cmd_help()
        return

    cmd  = argv[0].lower()
    rest = argv[1:]

    dispatch = {
        "--find":   lambda: cmd_find(rest),
        "--search": lambda: cmd_search(rest),
        "--new":    lambda: cmd_new(rest),
        "--add":    lambda: cmd_add(rest),
        "--edit":   lambda: cmd_edit(rest),
        "--del":    lambda: cmd_del(rest),
        "--list":   lambda: cmd_list(),
        "--export": lambda: cmd_export(rest),
        "--import": lambda: cmd_import(rest),
        "--prompt": lambda: cmd_prompt(rest),
        "--note":   lambda: cmd_note(rest),
    }

    if cmd in dispatch:
        dispatch[cmd]()
    else:
        warn(f"Unknown command: {cmd}")
        tip("Run  devref --help  for usage")


if __name__ == "__main__":
    main()
