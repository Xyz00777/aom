"""Inspect CLI commands for AOM (rebuilt).

The CLI exposes three invocations:

* ``aom inspect``         — launch the TUI on the most recent session.
* ``aom inspect --text``  — dump the most recent session as plain text.
* ``aom inspect prune``   — clean up old sessions on disk.

The legacy ``list`` / ``show`` / ``diff`` subcommands are removed;
chronological in-TUI navigation replaces them.

When stdout is not a TTY (CI, pipe, redirect), the no-arg invocation
falls back to ``--text`` automatically so scripts and SSH workflows
keep working.

See ``docs/superpowers/specs/2026-05-20-inspect-rebuild-design.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ansible_aom.inspect.text import render_session
from ansible_aom.session.store import (
    cleanup_old_sessions,
    find_latest_session,
    load_session,
)


def _default_state_dir() -> Path:
    return Path.home() / ".local" / "state" / "aom" / "sessions"


def _stdout_is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except AttributeError, ValueError:
        return False


def inspect_text(state_dir: Path) -> int:
    """Print the most-recent session as plain text. Return exit code."""
    latest = find_latest_session(state_dir)
    if latest is None:
        print(f"No sessions found in {state_dir}")
        return 0
    session = load_session(latest, state_dir)
    if session is None:
        print(f"Session not found: {latest}", file=sys.stderr)
        return 1
    print(render_session(session), end="")
    return 0


def inspect_tui(state_dir: Path) -> int:
    """Launch the TUI inspector. Returns the TUI's exit code."""
    # Lazy import: keeps `--text` invocation free of Textual cost.
    from ansible_aom.tui.screens.inspect import InspectApp

    latest = find_latest_session(state_dir)
    app = InspectApp(state_dir=state_dir, initial_session_id=latest)
    app.run()
    return 0


def inspect_prune(state_dir: Path, days: int) -> int:
    """Remove sessions older than ``days`` days."""
    deleted = cleanup_old_sessions(state_dir, keep_days=days)
    print(f"Pruned {deleted} session(s)")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aom inspect",
        description="Inspect AOM sessions",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=_default_state_dir(),
        help="Directory containing session data",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Render output as plain text instead of launching the TUI "
        "(also implied when stdout is not a TTY).",
    )
    sub = parser.add_subparsers(dest="command", help="Subcommand")

    prune = sub.add_parser("prune", help="Remove old sessions")
    prune.add_argument("--days", type=int, default=30, help="Remove sessions older than N days")

    return parser


def main(argv: list[str] | None = None) -> int:
    from ansible_aom.core import diagnostics

    diagnostics.install_from_env()

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "prune":
        return inspect_prune(args.state_dir, args.days)

    use_text = args.text or not _stdout_is_tty()
    if use_text:
        return inspect_text(args.state_dir)
    return inspect_tui(args.state_dir)


if __name__ == "__main__":
    sys.exit(main())
