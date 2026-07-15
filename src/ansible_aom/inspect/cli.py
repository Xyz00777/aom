"""Inspect CLI commands for AOM (rebuilt).

The CLI exposes three invocations:

* ``aom inspect``         — launch the TUI on the most recent session.
* ``aom inspect --text``  — dump the most recent session as plain text.
  ``--play`` and ``--task`` scope the verbose output to that play or task.
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

from ansible_aom.inspect.formatters import format_diagnostics_section
from ansible_aom.inspect.text import render_session, render_session_from_index
from ansible_aom.session.index import ensure_index
from ansible_aom.session.store import (
    cleanup_old_sessions,
    find_latest_session,
    load_session,
    load_session_meta,
)


def _default_state_dir() -> Path:
    return Path.home() / ".local" / "state" / "aom" / "sessions"


def _stdout_is_tty() -> bool:
    try:
        return sys.stdout.isatty()
    except AttributeError, ValueError:
        return False


def inspect_text(
    state_dir: Path,
    *,
    play_name: str | None = None,
    task_name: str | None = None,
) -> int:
    """Print the most-recent session as plain text. Return exit code.

    When ``play_name`` or ``task_name`` are given, the verbose section
    is scoped to that play or task.
    """
    latest = find_latest_session(state_dir)
    if latest is None:
        print(f"No sessions found in {state_dir}")
        return 0

    # Fast path: render from the derived sqlite index (built lazily for
    # legacy sessions, at end_session for new ones). Never parses the
    # full events.jsonl.
    session_path = state_dir / latest
    meta = load_session_meta(latest, state_dir)
    if meta is not None and ensure_index(session_path):
        text = render_session_from_index(
            session_path, meta, play_name=play_name, task_name=task_name
        )
        if text is not None:
            print(text, end="")
            return 0

    # Fallback: full-parse path (no events.jsonl on disk, or unreadable
    # index) — degrades to the pre-index behavior.
    session = load_session(latest, state_dir)
    if session is None:
        print(f"Session not found: {latest}", file=sys.stderr)
        return 1
    print(render_session(session, play_name=play_name, task_name=task_name), end="")
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


def inspect_debug(
    state_dir: Path,
    session_id: str | None = None,
    *,
    as_json: bool = False,
) -> int:
    """Print the diagnostics.json contents for ``session_id`` (or latest).

    ``as_json=True`` emits the raw record (or ``null`` for legacy
    sessions) to stdout for jq pipelines. The human-readable path
    keeps its session-header line for context.
    """
    import json as _json

    target = session_id or find_latest_session(state_dir)
    if target is None:
        if as_json:
            print(_json.dumps(None))
        else:
            print(f"No sessions found in {state_dir}")
        return 0
    # Meta-only load: diagnostics.json never needs the event log parsed.
    session = load_session_meta(target, state_dir)
    if session is None:
        print(f"Session not found: {target}", file=sys.stderr)
        return 1
    record = session.get("diagnostics")
    if as_json:
        print(_json.dumps(record))
        return 0
    print(f"Session {target}")
    print(format_diagnostics_section(record), end="")
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
    parser.add_argument(
        "--play",
        dest="play_name",
        default=None,
        help="With --text, scope verbose output to the named play.",
    )
    parser.add_argument(
        "--task",
        dest="task_name",
        default=None,
        help="With --text, scope verbose output to the named task.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the session's diagnostics.json summary (lifecycle "
        "timeline, event histogram, counters) and exit.",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="With --debug, emit the raw diagnostics.json record on stdout "
        "instead of the human-readable summary (for jq pipelines).",
    )
    parser.add_argument(
        "--session",
        dest="session_id",
        default=None,
        help="Specific session ID (default: most recent). Used with --debug.",
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

    if args.debug:
        return inspect_debug(args.state_dir, args.session_id, as_json=args.as_json)

    use_text = args.text or not _stdout_is_tty()
    if use_text:
        return inspect_text(
            args.state_dir,
            play_name=args.play_name,
            task_name=args.task_name,
        )
    return inspect_tui(args.state_dir)


if __name__ == "__main__":
    sys.exit(main())
