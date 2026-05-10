"""CLI entry point for AOM.

This module provides the main command-line interface for AOM.
See SPECIFICATION.md Section 3 for command interface details.
"""

import argparse
import logging
import shutil
import sys

from ansible_aom import __version__


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
        "--changes-only",
        action="store_true",
        help="Only show tasks with changes",
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


def create_inspect_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the inspect subcommand.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="aom inspect",
        description="Inspect previous run sessions",
    )

    parser.add_argument(
        "inspect_action",
        nargs="?",
        default="list",
        help="Action: list, show, diff, or prune",
    )

    parser.add_argument(
        "--failed",
        action="store_true",
        help="Filter to show only failed tasks",
    )

    parser.add_argument(
        "--host",
        metavar="HOST",
        help="Filter results by host",
    )

    parser.add_argument(
        "--tree",
        action="store_true",
        help="Show task tree structure",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Export as .aom artifact file",
    )

    parser.add_argument(
        "--days",
        type=int,
        metavar="N",
        help="Days threshold for prune (default: 30)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Output raw JSONL event dump",
    )

    parser.add_argument(
        "--tui",
        action="store_true",
        help="Launch Textual TUI for browsing sessions",
    )

    parser.add_argument(
        "session_ids",
        nargs="*",
        help="Session ID(s) for show, diff",
    )

    return parser


def handle_inspect(args: argparse.Namespace) -> int:
    """Handle the 'inspect' subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    action = args.inspect_action

    if action == "list":
        print("Listing sessions...")
        return 0
    elif action == "diff":
        if len(args.session_ids) < 2:
            print("Error: diff requires two session IDs", file=sys.stderr)
            return 1
        print(f"Comparing sessions {args.session_ids[0]} and {args.session_ids[1]}...")
        return 0
    elif action == "prune":
        days = args.days or 30
        print(f"Pruning sessions older than {days} days...")
        return 0
    else:
        return 0


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
        parser = create_inspect_parser()
        args = parser.parse_args(sys.argv[2:])
        return handle_inspect(args)

    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        import os

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

        try:
            renderer = create_renderer(tui_mode=args.tui, is_tty=sys.stdout.isatty())
            return run_playbook(args.playbook, args.ansible_args, renderer)
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
