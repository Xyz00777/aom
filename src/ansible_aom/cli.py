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
        description="Ansible Output Monitor - nom-style TUI for ansible-playbook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aom playbook.yml                      Run playbook with compact view
  aom --tui playbook.yml                Run playbook with full TUI
  aom playbook.yml -i inventory.ini     Pass options to ansible-playbook
  aom inspect list                      List all recorded sessions
  aom inspect <session-id>              Show session summary
  aom inspect diff <id1> <id2>          Compare two sessions
        """,
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch full multi-panel TUI instead of compact view",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print pre-execution diagnostics and enable DEBUG logging",
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

    if args.version:
        print(f"aom {__version__}")
        return 0

    if args.playbook:
        from ansible_aom.renderer.factory import create_renderer
        from ansible_aom.runner import run_playbook

        if detect_duplicate_playbook(args.playbook, args.ansible_args):
            print(
                f"aom: '{args.playbook}' appears twice on the command line — "
                "drop the trailing duplicate.",
                file=sys.stderr,
            )
            return 2

        ansible_args = ensure_inventory_arg(args.ansible_args)

        try:
            renderer = create_renderer(tui_mode=args.tui, is_tty=sys.stdout.isatty())
            return run_playbook(args.playbook, ansible_args, renderer)
        except KeyboardInterrupt:
            # The runner installs its own KeyboardInterrupt handling, but
            # an interrupt during renderer construction can still bubble up.
            print("Cancelled by user", file=sys.stderr)
            return 130
        except NotImplementedError:
            print("Renderer not yet implemented", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
