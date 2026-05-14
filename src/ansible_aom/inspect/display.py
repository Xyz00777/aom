"""Rich table formatting for AOM inspect output.

See SPECIFICATION.md Section 9.4 for output formats.
"""

from typing import Any

from ansible_aom.core.overhead import OverheadStats, analyze_overhead


def _fmt_seconds(value: float) -> str:
    """Render durations: sub-second as ms, anything else as s with one decimal."""
    if value < 1.0:
        return f"{int(round(value * 1000))} ms"
    return f"{value:.1f} s"


def format_overhead_section(stats: OverheadStats) -> str | None:
    """Render the per-task overhead summary for ``aom inspect show``.

    Returns ``None`` when there's literally nothing useful to display
    (no measurable samples at all). When samples exist but the P25
    threshold isn't met, returns a one-line acknowledgement so the user
    knows the analysis ran but had nothing to chew on.
    """
    if stats.samples == 0:
        return None

    lines = ["", "Per-task overhead (approximate):"]

    if stats.overhead_floor_s is None:
        lines.append(f"  insufficient data ({stats.samples} sample(s); need ≥ 4)")
        return "\n".join(lines)

    assert stats.median_duration_s is not None
    lines.append(
        f"  measured floor:    {_fmt_seconds(stats.overhead_floor_s)}"
        f"  (P25 of {stats.samples} host × task samples)"
    )
    lines.append(f"  median duration:   {_fmt_seconds(stats.median_duration_s)}")

    if stats.estimated_overhead_wall_s is not None:
        est = stats.estimated_overhead_wall_s
        if stats.overhead_share is not None:
            pct = stats.overhead_share * 100
            lines.append(
                f"  estimated setup time: ~{_fmt_seconds(est)} "
                f"({pct:.1f}% of {_fmt_seconds(stats.wall_clock_s or 0)} wall-clock)"
            )
        else:
            lines.append(f"  estimated setup time: ~{_fmt_seconds(est)}")

    return "\n".join(lines)


def format_session_table(sessions: list[dict[str, Any]]) -> str:
    """Format sessions as Rich table.

    Args:
        sessions: List of session dictionaries from list_sessions()

    Returns:
        Formatted table string for display
    """
    if not sessions:
        return "No sessions found"

    lines = []
    lines.append("Session ID  Playbook        Started               Status     Duration")
    lines.append("─" * 76)

    for session in sessions:
        short_id = session.get("short_id", session.get("session_id", "")[:8])
        playbook = session.get("playbook", "")
        start_time = session.get("start_time", "")
        status = session.get("status", "")
        duration = session.get("duration_seconds")

        if len(playbook) > 15:
            playbook = playbook[:12] + "..."

        duration_str = ""
        if duration is not None:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"

        line = f"{short_id:<11} {playbook:<15} {start_time:<21} {status:<10} {duration_str}"
        lines.append(line)

    return "\n".join(lines)


def format_session_summary(session: dict[str, Any]) -> str:
    """Format session summary as Rich output.

    Args:
        session: Session dictionary from load_session()

    Returns:
        Formatted summary string for display
    """
    lines = []

    lines.append(f"Session: {session.get('session_id', 'unknown')}")
    lines.append(f"Playbook: {session.get('playbook', 'unknown')}")
    lines.append(f"Status: {session.get('status', 'unknown')}")

    start_time = session.get("start_time")
    if start_time:
        lines.append(f"Started: {start_time}")

    end_time = session.get("end_time")
    if end_time:
        lines.append(f"Ended: {end_time}")

    duration = session.get("duration_seconds")
    if duration is not None:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        if hours > 0:
            lines.append(f"Duration: {hours}:{minutes:02d}:{seconds:02d}")
        else:
            lines.append(f"Duration: {minutes}:{seconds:02d}")

    malformed = session.get("malformed_lines", 0)
    if malformed > 0:
        lines.append(f"({malformed} malformed lines skipped)")

    lines.append("")
    lines.append("Plays:")

    events = session.get("events", [])
    play_events = [e for e in events if e.get("_event") == "v2_playbook_on_play_start"]

    for play_event in play_events:
        play = play_event.get("play", {})
        play_name = play.get("name", "unknown")
        lines.append(f"  • {play_name}")

    overhead = format_overhead_section(analyze_overhead(events))
    if overhead is not None:
        lines.append(overhead)

    return "\n".join(lines)


def format_diff_table(diff_result: dict[str, Any]) -> str:
    """Format diff result as Rich table.

    Args:
        diff_result: Dictionary from diff_sessions()

    Returns:
        Formatted table string for display
    """
    if not diff_result:
        return "No diff result"

    lines = []

    baseline = diff_result.get("baseline_playbook", "unknown")
    current = diff_result.get("current_playbook", "unknown")

    if diff_result.get("playbooks_differ"):
        lines.append(f"⚠ Warning: Different playbooks - baseline: {baseline}, current: {current}")
        lines.append("")

    lines.append(f"Comparing: {baseline} → {current}")
    lines.append("")
    lines.append("Task                          Baseline    Current    Classification")
    lines.append("─" * 76)

    tasks = diff_result.get("tasks", [])
    if not tasks:
        lines.append("No tasks to compare")
        return "\n".join(lines)

    for task in tasks:
        name = task.get("task_name", "")
        baseline_status = task.get("baseline_status") or "-"
        current_status = task.get("current_status") or "-"
        classification = task.get("classification", "unknown")

        if len(name) > 28:
            name = name[:25] + "..."

        line = f"{name:<29} {baseline_status:<11} {current_status:<10} {classification}"
        lines.append(line)

    return "\n".join(lines)


def format_tree_view(session: dict[str, Any]) -> str:
    """Format session as ASCII tree.

    Args:
        session: Session dictionary from load_session()

    Returns:
        Formatted tree string for display
    """
    lines = []

    playbook = session.get("playbook", "unknown")
    status = session.get("status", "unknown")

    lines.append(f"▶ {playbook} [{status}]")
    lines.append("")

    events = session.get("events", [])

    play_events = [e for e in events if e.get("_event") == "v2_playbook_on_play_start"]
    _ok_events = [e for e in events if e.get("_event") == "v2_runner_on_ok"]
    _failed_events = [e for e in events if e.get("_event") == "v2_runner_on_failed"]

    for play_event in play_events:
        play = play_event.get("play", {})
        play_name = play.get("name", "unknown")
        play_id = play.get("id")

        status_icon = "●"
        lines.append(f"  ▼ {status_icon} Play: {play_name}")

        task_events_for_play = []
        for event in events:
            if event.get("_event") in (
                "v2_runner_on_ok",
                "v2_runner_on_failed",
                "v2_runner_on_skipped",
                "v2_runner_on_unreachable",
            ):
                play_data = event.get("play", {})
                if play_data.get("id") == play_id:
                    task_events_for_play.append(event)

        seen_tasks = set()
        for event in task_events_for_play:
            task = event.get("task", {})
            task_id = task.get("id", "")
            task_name = task.get("name", "unknown")

            if task_id in seen_tasks:
                continue
            seen_tasks.add(task_id)

            event_type = event.get("_event")
            if event_type == "v2_runner_on_ok":
                hosts = event.get("hosts", {})
                if any(h.get("changed") for h in hosts.values()):
                    icon = "◆"
                else:
                    icon = "●"
            elif event_type == "v2_runner_on_failed":
                icon = "✖"
            elif event_type == "v2_runner_on_skipped":
                icon = "○"
            elif event_type == "v2_runner_on_unreachable":
                icon = "⊝"
            else:
                icon = "? "

            hosts = event.get("hosts", {})
            host_names = ", ".join(hosts.keys())

            lines.append(f"      {icon} {task_name:<30} {host_names}")

    return "\n".join(lines)
