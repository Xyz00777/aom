"""Plain-text rendering of an inspect session.

Used by ``aom inspect --text`` (and as the non-TTY fallback when stdout
isn't a terminal). Output is ANSI-free, deterministic, pipe-safe.

Consumes the same ``core.inspect_model`` builders the TUI uses, so the
two render the same information for the same session.
"""

from __future__ import annotations

from typing import Iterable, Iterator, Literal

from ansible_aom.core.inspect_model import (
    DetailBlock,
    RunSummary,
    StatusCounts,
    TaskTreeNode,
    build_detail_block,
    build_run_summary,
    build_task_tree,
    build_verbose_lines,
    task_ids_by_play,
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
    # JSONL timestamps are UTC; convert to the local system timezone for
    # display so users don't have to do the offset arithmetic in their head.
    lines = [
        f"Session  {summary.session_id}",
        f"Playbook {summary.playbook}",
    ]
    if summary.start_time:
        lines.append(f"Started  {summary.start_time.astimezone().isoformat(timespec='seconds')}")
    if summary.end_time:
        lines.append(f"Ended    {summary.end_time.astimezone().isoformat(timespec='seconds')}")
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
            elif child.kind == "task":
                # Nested include_tasks children: recurse so failures inside
                # an included file still surface.
                yield from _iter_failed_tasks(child)
    else:
        for child in node.children:
            yield from _iter_failed_tasks(child)


def _render_detail(block: DetailBlock) -> list[str]:
    lines: list[str] = []
    lines.append(f"Task:   {block.task_name}")
    if block.file_line:
        lines.append(f"File:   {block.file_line}")
    if block.host:
        lines.append(f"Host:   {block.host}")
    if block.action:
        lines.append(f"Action: {block.action}")
    if block.duration is not None:
        lines.append(f"Time:   {_fmt_duration(block.duration.total_seconds())}")
    lines.append(f"Status: {block.status}")
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
        lines.append("")
    if block.module_stderr and not block.failed_items:
        lines.append("  stderr:")
        for line in block.module_stderr.splitlines():
            lines.append(f"    {line}")
        lines.append("")
    if block.module_stdout:
        lines.append("  stdout:")
        for line in block.module_stdout.splitlines():
            lines.append(f"    {line}")
        lines.append("")
    if block.warnings:
        lines.append("  warnings:")
        for w in block.warnings:
            lines.append(f"    ⚠ {w}")
        lines.append("")
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


def _render_verbose(
    session: dict,
    tree: TaskTreeNode,
    *,
    play_name: str | None = None,
    task_name: str | None = None,
) -> list[str]:
    """Render the verbose/stderr section from ``aom_stderr_line`` events.

    Uses ``build_verbose_lines`` to scope lines by play and task.
    With no scope (the default), shows all run-level lines. With
    ``play_name``, shows run-level plus task-level lines for that play.
    With ``task_name``, shows run-level plus lines for the matching task
    (resolved via the task tree).

    The old ``_render_stderr_tail`` was gated on ``status == "failed"``
    and capped at 20 lines. This replacement shows verbose output for
    every session and removes the cap.
    """
    level: Literal["run", "play", "task"] = "run"
    play = play_name
    task_id: str | None = None
    host: str | None = None

    if task_name:
        level = "task"
        for node in _iter_tree(tree):
            if node.kind == "task" and node.label == task_name and node.task_id:
                task_id = node.task_id
                for child in node.children:
                    if child.kind == "host":
                        host = child.label
                        break
                break
        if not play:
            play = _play_name_for_task(tree, task_id)
    elif play_name:
        level = "play"

    lines = build_verbose_lines(
        session,
        level=level,
        play_name=play,
        task_id=task_id,
        host=host,
        play_task_ids=task_ids_by_play(tree),
    )
    if not lines:
        return []

    header = "Verbose"
    if play_name and not task_name:
        header = f"Verbose (play: {play_name})"
    elif task_name:
        scope = f"task: {task_name}"
        if play_name:
            scope = f"play: {play_name}, {scope}"
        header = f"Verbose ({scope})"

    return ["", header, "─" * len(header)] + [f"  {line}" for line in lines]


def _iter_tree(node: TaskTreeNode) -> Iterator[TaskTreeNode]:
    """Yield all nodes in the tree depth-first."""
    yield node
    for child in node.children:
        yield from _iter_tree(child)


def _play_name_for_task(tree: TaskTreeNode, task_id: str | None) -> str | None:
    """Find the play name containing the given task_id."""
    if not task_id:
        return None
    for play in tree.children:
        if play.kind != "play":
            continue
        for node in _iter_tree(play):
            if node.kind == "task" and node.task_id == task_id:
                return play.label
    return None


def render_session(
    session: dict, *, play_name: str | None = None, task_name: str | None = None
) -> str:
    """Render a session dict as plain text. ANSI-free, deterministic.

    When ``play_name`` or ``task_name`` are given, the verbose section is
    scoped to that play or task. Failures are always shown (they are not
    affected by scope).
    """
    summary = build_run_summary(session)
    tree = build_task_tree(session)
    parts: list[str] = []
    parts.extend(_render_header(summary))
    parts.extend(_render_failures(session, tree))
    parts.extend(_render_verbose(session, tree, play_name=play_name, task_name=task_name))
    return "\n".join(parts) + "\n"


def render_session_list(summaries: Iterable[RunSummary]) -> str:
    """Render a list of run summaries as a plain-text table.

    Library helper; not currently wired to a CLI command (the new CLI
    has no explicit `list` subcommand). Kept for non-TTY/test reuse.
    """
    rows = ["Date              Playbook                Dur   Status"]
    rows.append("─" * 64)
    for s in summaries:
        date = s.start_time.astimezone().strftime("%Y-%m-%d %H:%M") if s.start_time else "—"
        dur = _fmt_duration(s.duration.total_seconds() if s.duration else None)
        playbook = s.playbook if len(s.playbook) <= 22 else s.playbook[:19] + "..."
        rows.append(f"{date:<17} {playbook:<22}  {dur:>5}  {s.status}")
    return "\n".join(rows) + "\n"
