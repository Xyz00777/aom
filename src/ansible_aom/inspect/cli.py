"""Inspect CLI commands for AOM.

See SPECIFICATION.md Section 3.3 for inspect subcommand details.
"""

import argparse
import json
import sys
from pathlib import Path

from ansible_aom.core.session import cleanup_old_sessions, list_sessions, load_session
from ansible_aom.inspect.diff import diff_sessions
from ansible_aom.inspect.display import (
    format_diff_table,
    format_session_summary,
    format_session_table,
    format_tree_view,
)


def inspect_list(state_dir: Path, output_format: str = "table") -> int:
    """List all sessions.

    Args:
        state_dir: Directory containing session data
        output_format: Output format ('table', 'json', 'jsonl')

    Returns:
        Exit code (0 for success)
    """
    sessions = list_sessions(state_dir)

    if output_format == "json":
        print(json.dumps(sessions, indent=2))
    elif output_format == "jsonl":
        for session in sessions:
            print(json.dumps(session))
    else:
        output = format_session_table(sessions)
        print(output)

    return 0


def inspect_show(
    session_id: str,
    state_dir: Path,
    failed_only: bool = False,
    host_filter: str | None = None,
    show_tree: bool = False,
    output_format: str = "table",
) -> int:
    """Show session summary.

    Args:
        session_id: Session ID to show
        state_dir: Directory containing session data
        failed_only: If True, show only failed tasks
        host_filter: Filter to tasks for specific host
        show_tree: If True, show ASCII tree view
        output_format: Output format ('table', 'json', 'jsonl')

    Returns:
        Exit code (0 for success, 1 for not found)
    """
    session = load_session(session_id, state_dir)

    if session is None:
        print(f"Session not found: {session_id}", file=sys.stderr)
        return 1

    if failed_only:
        session = _filter_failed(session)

    if host_filter:
        session = _filter_by_host(session, host_filter)

    if output_format == "json":
        print(json.dumps(session, indent=2))
    elif output_format == "jsonl":
        events = session.get("events", [])
        for event in events:
            print(json.dumps(event))
    elif show_tree:
        output = format_tree_view(session)
        print(output)
    else:
        output = format_session_summary(session)
        print(output)

    return 0


def inspect_diff(
    session_id_1: str,
    session_id_2: str,
    state_dir: Path,
    changes_only: bool = False,
    output_format: str = "table",
) -> int:
    """Compare two sessions.

    Args:
        session_id_1: Baseline session ID
        session_id_2: Current session ID
        state_dir: Directory containing session data
        changes_only: If True, show only changed tasks
        output_format: Output format ('table', 'json')

    Returns:
        Exit code (0 for success, 1 for not found)
    """
    session1 = load_session(session_id_1, state_dir)
    session2 = load_session(session_id_2, state_dir)

    if session1 is None:
        print(f"Session not found: {session_id_1}", file=sys.stderr)
        return 1

    if session2 is None:
        print(f"Session not found: {session_id_2}", file=sys.stderr)
        return 1

    result = diff_sessions(session1, session2, changes_only=changes_only)

    if output_format == "json":
        print(json.dumps(result, indent=2))
    else:
        output = format_diff_table(result)
        print(output)

    return 0


def inspect_prune(state_dir: Path, days: int = 30) -> int:
    """Cleanup old sessions.

    Args:
        state_dir: Directory containing session data
        days: Remove sessions older than this many days

    Returns:
        Exit code (0 for success)
    """
    deleted = cleanup_old_sessions(state_dir, keep_days=days)
    print(f"Pruned {deleted} session(s)")
    return 0


def _filter_failed(session: dict) -> dict:
    """Filter session events to only include failed tasks."""
    filtered_events = []
    for event in session.get("events", []):
        event_type = event.get("_event", "")
        if event_type == "v2_runner_on_failed":
            filtered_events.append(event)
        elif event_type == "v2_runner_on_unreachable":
            filtered_events.append(event)
        elif event_type in (
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ):
            filtered_events.append(event)

    result = dict(session)
    result["events"] = filtered_events
    return result


def _filter_by_host(session: dict, hostname: str) -> dict:
    """Filter session events to only include tasks for a specific host."""
    filtered_events = []
    for event in session.get("events", []):
        hosts = event.get("hosts", {})
        if hosts and hostname in hosts:
            filtered_events.append(event)
        elif event.get("_event") in (
            "v2_playbook_on_start",
            "v2_playbook_on_play_start",
            "v2_playbook_on_stats",
        ):
            filtered_events.append(event)

    result = dict(session)
    result["events"] = filtered_events
    return result


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for inspect commands.

    Args:
        argv: Argument list. If None, parses from sys.argv. The top-level
            ``aom inspect ...`` dispatcher passes ``sys.argv[2:]`` so the
            ``inspect`` token is consumed before this parser runs.
    """
    parser = argparse.ArgumentParser(description="Inspect AOM sessions")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session data",
    )

    list_parser = subparsers.add_parser("list", help="List all sessions")
    list_parser.add_argument("--failed", action="store_true", help="Show only failed sessions")
    list_parser.add_argument("--host", type=str, help="Filter by hostname")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    list_parser.add_argument("--jsonl", action="store_true", help="Output as JSONL")

    show_parser = subparsers.add_parser("show", help="Show session summary")
    show_parser.add_argument("session_id", help="Session ID to show")
    show_parser.add_argument("--failed", action="store_true", help="Show only failed tasks")
    show_parser.add_argument("--host", type=str, help="Filter by hostname")
    show_parser.add_argument("--tree", action="store_true", help="Show ASCII tree view")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.add_argument("--jsonl", action="store_true", help="Output as JSONL")

    diff_parser = subparsers.add_parser("diff", help="Compare two sessions")
    diff_parser.add_argument("session_id_1", help="Baseline session ID")
    diff_parser.add_argument("session_id_2", help="Current session ID")
    diff_parser.add_argument("--changes-only", action="store_true", help="Show only changed tasks")
    diff_parser.add_argument("--json", action="store_true", help="Output as JSON")

    prune_parser = subparsers.add_parser("prune", help="Cleanup old sessions")
    prune_parser.add_argument(
        "--days", type=int, default=30, help="Remove sessions older than N days"
    )

    args = parser.parse_args(argv)

    if args.command == "list":
        if getattr(args, "jsonl", False):
            output_format = "jsonl"
        elif getattr(args, "json", False):
            output_format = "json"
        else:
            output_format = "table"
        return inspect_list(args.state_dir, output_format)
    elif args.command == "show":
        if getattr(args, "jsonl", False):
            output_format = "jsonl"
        elif getattr(args, "json", False):
            output_format = "json"
        else:
            output_format = "table"
        return inspect_show(
            args.session_id,
            args.state_dir,
            failed_only=getattr(args, "failed", False),
            host_filter=getattr(args, "host", None),
            show_tree=getattr(args, "tree", False),
            output_format=output_format,
        )
    elif args.command == "diff":
        output_format = "json" if getattr(args, "json", False) else "table"
        return inspect_diff(
            args.session_id_1,
            args.session_id_2,
            args.state_dir,
            changes_only=getattr(args, "changes_only", False),
            output_format=output_format,
        )
    elif args.command == "prune":
        return inspect_prune(args.state_dir, args.days)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
