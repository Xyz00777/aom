"""Display helpers for AOM inspect output.

Houses both the overhead-stats summary (legacy) and the
``aom inspect --debug`` diagnostics formatter (phase 6 of the
diagnostics-layer plan).
"""

from __future__ import annotations

from typing import Any

from ansible_aom.core.overhead import OverheadStats


def _fmt_seconds(value: float) -> str:
    """Render durations: sub-second as ms, anything else as s with one decimal."""
    if value < 1.0:
        return f"{int(round(value * 1000))} ms"
    return f"{value:.1f} s"


def format_overhead_section(stats: OverheadStats) -> str | None:
    """Render the per-task overhead summary.

    Returns ``None`` when there's literally nothing useful to display
    (no measurable samples at all). When samples exist but the P25
    threshold isn't met, returns a one-line acknowledgement so the
    caller knows the analysis ran but had nothing to chew on.
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


def format_diagnostics_section(record: dict[str, Any] | None) -> str:
    """Render the ``diagnostics.json`` payload as a plain-text section.

    Returns a fallback string when ``record`` is None (session predates
    the diagnostics layer or the file was unreadable) so the caller can
    print unconditionally.

    Sections, in order:
    1. Lifecycle deltas (relative to the first mark, in ms).
    2. Counters from the runner-side accumulator + renderer stats.
    3. Resource peaks (max RSS, tracemalloc).
    4. Event histogram sorted by count descending.
    5. Env snapshot (only the keys actually captured at run time).
    6. Recording-disabled reason if applicable.
    """
    if record is None:
        return (
            "No diagnostics available for this session "
            "(recorded before the diagnostics layer landed).\n"
        )

    lines: list[str] = []
    schema = record.get("schema_version", "?")
    lines.append(f"Diagnostics (schema v{schema})")

    warnings = record.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in warnings:
            lines.append(f"  ! {w}")
    aom_version = record.get("aom_version")
    if aom_version:
        lines.append(f"  aom version: {aom_version}")
    host_count = record.get("host_count")
    task_count = record.get("playbook_task_count")
    if host_count is not None or task_count is not None:
        lines.append(
            f"  hosts: {host_count if host_count is not None else '?'}, "
            f"tasks: {task_count if task_count is not None else '?'}"
        )

    lifecycle = record.get("lifecycle") or {}
    if lifecycle:
        lines.append("")
        lines.append("Lifecycle (ms from first mark):")
        for name, ms in lifecycle.items():
            lines.append(f"  {name:<24} {ms:>8} ms")

    counters = record.get("counters") or {}
    if counters:
        lines.append("")
        lines.append("Counters:")
        # Stable order; hide the boolean+reason here (surfaced separately).
        for key in (
            "events_received",
            "render_calls",
            "log_writes",
            "pty_bytes",
            "pexpect_timeouts",
            "stall_count_max",
        ):
            if key in counters:
                lines.append(f"  {key:<24} {counters[key]:>10}")

    resources = record.get("resources") or {}
    if any(v is not None for v in resources.values()):
        lines.append("")
        lines.append("Resources:")
        for key, value in resources.items():
            if value is None:
                continue
            lines.append(f"  {key:<24} {value:>10}")

    histogram = record.get("event_histogram") or {}
    if histogram:
        lines.append("")
        lines.append("Event histogram (by count desc):")
        for name, count in sorted(histogram.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {name:<40} {count:>8}")

    env = record.get("env_snapshot") or {}
    if env:
        lines.append("")
        lines.append("Env snapshot:")
        for key in sorted(env):
            lines.append(f"  {key}={env[key]}")

    if counters.get("session_recording_disabled"):
        reason = counters.get("session_disable_reason") or "unknown"
        lines.append("")
        lines.append(f"Session recording disabled mid-run: {reason}")

    return "\n".join(lines) + "\n"


def format_changes_section(
    records: list[Any],
    *,
    session_id: str | None = None,
    show_diff: bool = False,
) -> str:
    """Format TaskChangeRecords as human-readable plain text."""
    lines: list[str] = []
    if session_id:
        lines.append(f"Session: {session_id}")
    lines.append(f"Changed Tasks ({len(records)}):")
    if not records:
        lines.append("  No tasks reported changed status.")
        return "\n".join(lines) + "\n"

    for idx, rec in enumerate(records, 1):
        lines.append("")
        lines.append(f"[{idx}] {rec.task_name}")
        lines.append(f"    Play:     {rec.play_name}")
        if rec.role:
            lines.append(f"    Role:     {rec.role}")
        if rec.file_line:
            lines.append(f"    File:     {rec.file_line}")
        if rec.action:
            lines.append(f"    Action:   {rec.action}")
        lines.append(f"    Host:     {rec.host}")

        if rec.cmd:
            lines.append(f"    Command:  {rec.cmd}")
        if rec.msg:
            lines.append(f"    Message:  {rec.msg}")
        if rec.details:
            det_parts = [f"{k}={v}" for k, v in sorted(rec.details.items())]
            lines.append(f"    Details:  {' '.join(det_parts)}")

        if rec.changed_items:
            lines.append(f"    Changed items ({len(rec.changed_items)}):")
            for item in rec.changed_items:
                lines.append(f"      • {item.label}")
                if item.msg:
                    lines.append(f"          msg: {item.msg}")

        if rec.stdout:
            lines.append("    Stdout:")
            for line in rec.stdout.splitlines():
                lines.append(f"      {line}")
        if rec.stderr:
            lines.append("    Stderr:")
            for line in rec.stderr.splitlines():
                lines.append(f"      {line}")

        if show_diff and rec.diff:
            lines.append("    Diff:")
            if isinstance(rec.diff, list):
                for d in rec.diff:
                    if isinstance(d, dict):
                        b_hdr = d.get("before_header") or d.get("before")
                        a_hdr = d.get("after_header") or d.get("after")
                        if "before" in d and "after" in d:
                            lines.append(f"      --- before: {b_hdr}")
                            lines.append(f"      +++ after:  {a_hdr}")
                            for line_str in str(d["before"]).splitlines():
                                lines.append(f"      - {line_str}")
                            for line_str in str(d["after"]).splitlines():
                                lines.append(f"      + {line_str}")
                        elif "prepared" in d:
                            for line_str in str(d["prepared"]).splitlines():
                                lines.append(f"      {line_str}")
                    else:
                        lines.append(f"      {d}")
            elif isinstance(rec.diff, dict):
                if "prepared" in rec.diff:
                    for line_str in str(rec.diff["prepared"]).splitlines():
                        lines.append(f"      {line_str}")
                elif "before" in rec.diff and "after" in rec.diff:
                    lines.append("      --- before")
                    lines.append("      +++ after")
                    for line_str in str(rec.diff["before"]).splitlines():
                        lines.append(f"      - {line_str}")
                    for line_str in str(rec.diff["after"]).splitlines():
                        lines.append(f"      + {line_str}")
            elif isinstance(rec.diff, str):
                for line_str in rec.diff.splitlines():
                    lines.append(f"      {line_str}")

    return "\n".join(lines) + "\n"


def format_changes_json(
    records: list[Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Serialize TaskChangeRecords to a dictionary for JSON output."""
    changes: list[dict[str, Any]] = []
    for r in records:
        changes.append(
            {
                "play_name": r.play_name,
                "role": r.role,
                "task_name": r.task_name,
                "file_line": r.file_line,
                "action": r.action,
                "host": r.host,
                "duration_seconds": r.duration.total_seconds() if r.duration else None,
                "cmd": r.cmd,
                "msg": r.msg,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "diff": r.diff,
                "changed_items": [
                    {"label": it.label, "msg": it.msg, "stderr": it.stderr}
                    for it in r.changed_items
                ],
                "details": r.details,
            }
        )
    return {
        "session_id": session_id,
        "total_changes": len(records),
        "changes": changes,
    }


def format_warnings_section(
    records: list[Any],
    *,
    session_id: str | None = None,
) -> str:
    """Format WarningRecords as human-readable plain text."""
    lines: list[str] = []
    if session_id:
        lines.append(f"Session: {session_id}")
    lines.append(f"Warnings & Deprecations ({len(records)}):")
    if not records:
        lines.append("  No warnings or deprecations recorded.")
        return "\n".join(lines) + "\n"

    for idx, rec in enumerate(records, 1):
        tag = "[DEPRECATION]" if rec.warning_type == "deprecation" else "[WARNING]"
        lines.append("")
        lines.append(f"[{idx}] {tag}")
        if rec.task_name:
            lines.append(f"    Task:     {rec.task_name}")
        if rec.play_name:
            lines.append(f"    Play:     {rec.play_name}")
        if rec.role:
            lines.append(f"    Role:     {rec.role}")
        if rec.file_line:
            lines.append(f"    File:     {rec.file_line}")
        if rec.host:
            lines.append(f"    Host:     {rec.host}")
        lines.append(f"    Message:  {rec.message}")

    return "\n".join(lines) + "\n"


def format_warnings_json(
    records: list[Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Serialize WarningRecords to a dictionary for JSON output."""
    warnings: list[dict[str, Any]] = []
    for r in records:
        warnings.append(
            {
                "warning_type": r.warning_type,
                "message": r.message,
                "play_name": r.play_name,
                "role": r.role,
                "task_name": r.task_name,
                "file_line": r.file_line,
                "host": r.host,
            }
        )
    return {
        "session_id": session_id,
        "total_warnings": len(records),
        "warnings": warnings,
    }
