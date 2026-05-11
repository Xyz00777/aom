"""CLI entry point for AOM.

This module provides the main command-line interface for AOM.
See SPECIFICATION.md Section 3 for command interface details.
"""

import argparse
import logging
import os
import shutil
import sys

from ansible_aom import __version__

# Files we'll auto-discover as inventory when the user doesn't pass -i.
# Order is preference order — `inventory.ini` wins over `hosts` because
# the former is more specific to ansible's conventions.
_DEFAULT_INVENTORY_NAMES = (
    "inventory.ini",
    "inventory.yml",
    "inventory.yaml",
    "inventory",
    "hosts.ini",
    "hosts.yml",
    "hosts.yaml",
    "hosts",
)

# All flags ansible-playbook accepts for specifying inventory; if the user
# already supplied any of these we leave their args alone.
_INVENTORY_FLAGS = ("-i", "--inventory", "--inventory-file")


def detect_default_inventory() -> str | None:
    """Return the first conventional inventory file found in CWD, or None."""
    for name in _DEFAULT_INVENTORY_NAMES:
        if os.path.isfile(name):
            return name
    return None


def detect_duplicate_playbook(playbook: str, ansible_args: list[str]) -> bool:
    """True if `playbook` appears (path-normalised) in `ansible_args`.

    Catches the easy typo where the user types
    `aom site.yml -i inv.ini site.yml` — the trailing copy lands in
    ansible_args via argparse REMAINDER, ansible-playbook then dies
    with an unhelpful argparse error. Surfacing it earlier saves the
    user a confused moment.
    """
    target = os.path.normpath(playbook)
    return any(os.path.normpath(arg) == target for arg in ansible_args)


def ensure_inventory_arg(ansible_args: list[str]) -> list[str]:
    """If no -i/--inventory flag is set, prepend one pointing at the default file.

    A no-op when the user already supplied an inventory or no default exists.
    Returns the (possibly modified) args list — never mutates the input.
    """
    if any(arg in _INVENTORY_FLAGS or arg.startswith("--inventory=") for arg in ansible_args):
        return ansible_args
    default = detect_default_inventory()
    if default is None:
        return ansible_args
    return ["-i", default, *ansible_args]


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the AOM CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="aom",
        description="Ansible Output Monitor — nom-style live view for ansible-playbook.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aom playbook.yml                      Run playbook with compact view (default)
  aom --tui playbook.yml                Run with the full multi-panel TUI
  aom playbook.yml -i inv.ini -v        Flags after the playbook are forwarded
  aom playbook.yml -vvv --tags=deploy   …including ansible-playbook's own -v / -vv / -vvv
  aom inspect list                      List all recorded sessions
  aom inspect <session-id>              Show one session's summary
  aom inspect <session-id> --tree       Tree view of plays/tasks/hosts
  aom inspect <session-id> --failed     Only the failed tasks
  aom inspect diff <id1> <id2>          Diff two sessions
  aom inspect prune --days 30           Delete sessions older than N days

Argument forwarding:
  Anything after the playbook path is passed verbatim to ansible-playbook.
  AOM never silently rewrites flags. If you pass -i / --inventory, AOM
  leaves your inventory alone; otherwise AOM auto-detects ./inventory.ini
  (then .yml, .yaml, hosts) and prepends -i for convenience.

Verbosity:
  AOM's own debug flag is --verbose (long form only). The short -v
  is reserved for ansible-playbook, so `aom site.yml -v` raises
  ansible verbosity, not AOM verbosity.

Session recording:
  Every run writes ~/.local/state/aom/sessions/<uuidv7>/ containing
  events.jsonl, stderr.log, and meta.json. Recording is best-effort —
  disk errors are logged but never abort the run. Use `aom inspect`
  to replay past runs; `aom inspect prune` to clean up.

File locations:
  Sessions:    ~/.local/state/aom/sessions/<uuidv7>/
  Config:      ~/.config/aom/config.yaml (optional)
  Inventory:   auto-detects ./inventory.ini, ./inventory.yml,
               ./inventory.yaml, ./inventory, ./hosts.ini, ./hosts.yml,
               ./hosts.yaml, ./hosts (first match wins).

Exit codes:
  0   playbook completed cleanly
  1   playbook failed, or AOM crashed
  2   ansible-playbook reported unreachable hosts, or AOM detected
      a CLI usage error (e.g. duplicate playbook positional)
  127 ansible-playbook executable not found
  130 cancelled by user (Ctrl+C)

See README.md and SPECIFICATION.md in the source tree for full details.
        """,
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch full multi-panel TUI instead of compact view",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print AOM pre-execution diagnostics and enable DEBUG logging",
    )

    parser.add_argument(
        "playbook",
        nargs="?",
        default=None,
        help="Playbook file to run",
    )

    parser.add_argument(
        "ansible_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed to ansible-playbook",
    )

    return parser


def _run_compact(playbook: str, ansible_args: list[str]) -> int:
    """Spawn the legacy compact renderer via ``run_playbook``.

    The compact path stays synchronous: ``run_playbook`` owns the
    pexpect loop, the renderer prints to stdout, no Textual involved.
    """
    from ansible_aom.renderer.factory import create_renderer
    from ansible_aom.runner import run_playbook

    try:
        renderer = create_renderer(tui_mode=False, is_tty=sys.stdout.isatty())
        return run_playbook(playbook, ansible_args, renderer)
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_tui(playbook: str, ansible_args: list[str]) -> int:
    """Launch the Textual TUI and let it drive the runner.

    AOMApp owns its own event loop (``app.run()``) and pumps the
    pexpect runner from a worker thread. The exit code is whatever
    ``run_playbook`` returned, reachable on ``app.exit_code`` after
    ``app.run()`` returns. ``None`` (user quit before completion) maps
    to exit 1 — we treat an aborted-by-quit run as non-success without
    pretending to know the playbook's true outcome.
    """
    from ansible_aom.tui.app import AOMApp

    try:
        app = AOMApp(playbook=playbook, ansible_args=ansible_args)
        app.run()
    except KeyboardInterrupt:
        print("Cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    exit_code = app.exit_code
    return exit_code if exit_code is not None else 1


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    if "--version" in sys.argv:
        print(f"aom {__version__}")
        return 0

    if "--help" in sys.argv or "-h" in sys.argv:
        create_parser().print_help()
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        from ansible_aom.inspect.cli import main as inspect_main

        return inspect_main(sys.argv[2:])

    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        aom_logger = logging.getLogger("ansible_aom")
        aom_logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        aom_logger.addHandler(console_handler)

        ansible_path = shutil.which("ansible-playbook")
        print(f"ansible-playbook path: {ansible_path or 'not found'}")
        print(f"ANSIBLE_STDOUT_CALLBACK: {os.environ.get('ANSIBLE_STDOUT_CALLBACK', '(not set)')}")
        print(f"Terminal: tty={sys.stdout.isatty()}, columns={shutil.get_terminal_size().columns}")
        aom_logger.debug("--list-tasks summary: verbose mode enabled, diagnostics printed")

    if args.playbook:
        if detect_duplicate_playbook(args.playbook, args.ansible_args):
            print(
                f"aom: '{args.playbook}' appears twice on the command line — "
                "drop the trailing duplicate.",
                file=sys.stderr,
            )
            return 2

        ansible_args = ensure_inventory_arg(args.ansible_args)

        if args.tui:
            return _run_tui(args.playbook, ansible_args)
        return _run_compact(args.playbook, ansible_args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
