"""Plain-text rendering of an inspect session.

Used by ``aom inspect --text`` (and as the non-TTY fallback when stdout
isn't a terminal). Output is ANSI-free, deterministic, pipe-safe.

Consumes the same ``core.inspect_model`` builders the TUI uses, so the
two render the same information for the same session.
"""

from __future__ import annotations

from typing import Iterable, Iterator

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
)


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, sec = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{sec:02d}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h{mins:02d}m{sec:02d}s"


def _host_counts_line(host: str, counts: StatusCounts) -> str:
    parts: list[str] = []
    if counts.ok:
        parts.append(f"{counts.ok} ok")
    if counts.changed:
        parts.append(f"{counts.changed} changed")
    if counts.failed:
        parts.append(f"{counts.failed} failed")
    if counts.unreachable:
        parts.append(f"{counts.unreachable} unreachable")
    if counts.skipped:
        parts.append(f"{counts.skipped} skipped")
    body = ", ".join(parts) or "no events"
    return f"  {host}: {body}"


def _render_header(summary: RunSummary) -> list[str]:
    lines = [
        f"Session  {summary.session_id}",
        f"Playbook {summary.playbook}",
    ]
    if summary.start_time:
        lines.append(f"Started  {summary.start_time.isoformat().replace('+00:00', 'Z')}")
    if summary.end_time:
        lines.append(f"Ended    {summary.end_time.isoformat().replace('+00:00', 'Z')}")
    dur = summary.duration.total_seconds() if summary.duration else None
    lines.append(f"Duration {_fmt_duration(dur)}")
    lines.append(f"Status   {summary.status}")
    if summary.host_counts:
        lines.append("")
        lines.append("Stats")
        for host, counts in sorted(summary.host_counts.items()):
            lines.append(_host_counts_line(host, counts))
    return lines


def _iter_failed_tasks(
    node: TaskTreeNode,
) -> Iterator[tuple[TaskTreeNode, TaskTreeNode]]:
    """Walk the tree yielding (task_node, host_node) for every failed/unreachable host."""
    if node.kind == "task":
        for child in node.children:
            if child.kind == "host" and (child.stats.failed or child.stats.unreachable):
                yield node, child
    else:
        for child in node.children:
            yield from _iter_failed_tasks(child)


def _render_detail(block: DetailBlock) -> list[str]:
    lines: list[str] = []
    lines.append(f"Task: {block.task_name}")
    if block.file_line:
        lines.append(f"File: {block.file_line}")
    if block.host:
        lines.append(f"Host: {block.host}")
    if block.duration is not None:
        lines.append(f"Time: {_fmt_duration(block.duration.total_seconds())}")
    lines.append("")
    if block.msg:
        lines.append(f"  msg: {block.msg}")
        lines.append("")
    if block.failed_items:
        total = len(block.failed_items) + len(block.ok_items)
        lines.append(f"  Failed items ({len(block.failed_items)} of {total}):")
        for item in block.failed_items:
            lines.append(f"    ✖ {item.label}")
            if item.msg:
                lines.append(f"        {item.msg}")
            if item.stderr:
                lines.append(f"        stderr: {item.stderr}")
        if block.ok_items:
            lines.append(
                f"  ({len(block.ok_items)} ok item{'s' if len(block.ok_items) != 1 else ''})"
            )
    if block.module_stderr and not block.failed_items:
        lines.append("  stderr:")
        for line in block.module_stderr.splitlines():
            lines.append(f"    {line}")
    return lines


def _render_failures(session: dict, tree: TaskTreeNode) -> list[str]:
    pairs = list(_iter_failed_tasks(tree))
    if not pairs:
        return []
    lines = ["", f"Failures ({len(pairs)})", "─" * 13]
    for task_node, host_node in pairs:
        block = build_detail_block(session, task_node, host_node)
        lines.extend(_render_detail(block))
        lines.append("")
    return lines


def _render_stderr_tail(session: dict, max_lines: int = 20) -> list[str]:
    tail: list[str] = (session.get("stderr") or [])[-max_lines:]
    if not tail:
        return []
    return ["stderr.log (tail)", "─" * 17, *tail]


def render_session(session: dict) -> str:
    """Render a session dict as plain text. ANSI-free, deterministic."""
    summary = build_run_summary(session)
    tree = build_task_tree(session)
    parts: list[str] = []
    parts.extend(_render_header(summary))
    parts.extend(_render_failures(session, tree))
    if summary.status == "failed":
        parts.append("")
        parts.extend(_render_stderr_tail(session))
    return "\n".join(parts) + "\n"


def render_session_list(summaries: Iterable[RunSummary]) -> str:
    """Render a list of run summaries as a plain-text table.

    Library helper; not currently wired to a CLI command (the new CLI
    has no explicit `list` subcommand). Kept for non-TTY/test reuse.
    """
    rows = ["Date              Playbook                Dur   Status"]
    rows.append("─" * 64)
    for s in summaries:
        date = s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "—"
        dur = _fmt_duration(s.duration.total_seconds() if s.duration else None)
        playbook = s.playbook if len(s.playbook) <= 22 else s.playbook[:19] + "..."
        rows.append(f"{date:<17} {playbook:<22}  {dur:>5}  {s.status}")
    return "\n".join(rows) + "\n"
