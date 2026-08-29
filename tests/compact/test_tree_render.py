"""Snapshot tests for the compact renderer's tree + host-row block.

These pin the rendered text shape. Updates require explicit golden
changes — adjust the expected strings when you intentionally change
formatting, not when you accidentally do.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import format_host_rows, format_tree_block
from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import TreeLine, TreeProjection


def _state(*events: dict) -> RunState:
    s = RunState(playbook="site.yml")
    for e in events:
        s.handle_event(e)
    return s


def test_format_host_rows_running_host_includes_current_task_suffix():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        },
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    # New table layout: header + 1 host row.
    assert len(rows) == 2
    assert "host" in rows[0]
    assert "web1" in rows[1]
    # Current-task column ("on") shows just the task name; the column
    # header is what tells the user this is the in-flight task.
    assert "Install nginx" in rows[1]
    assert "◐" in rows[1]


def test_format_host_rows_idle_host_shows_idle_marker():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        },
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    # Header is rows[0]; first host row is rows[1].
    assert "(idle)" in rows[1]
    # Count cells are bare numbers now (icons removed; the column
    # header carries the label).
    assert " 1 " in rows[1]


def test_format_host_rows_unreachable_host_shows_unreachable():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"db1": {"unreachable": True}},
        },
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    # Header has an "unreachable" column. Host row suffix now shows the
    # task name with the ⊝ glyph (not the bare word "unreachable").
    assert "unreachable" in rows[0]
    assert "⊝ Install nginx" in rows[1]
    # Bare count of 1 lands in the unreachable column.
    assert "1" in rows[1]


def test_format_host_rows_two_space_column_separator():
    """Regression guard: spacing between count cells and the suffix is
    two spaces (not one, not three). Pins the visual separator so future
    refactors of the join logic don't silently shift the gap."""
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        },
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    # Columns join on two-space gaps. The exact alignment depends on
    # column widths, but the suffix "(idle)" must be preceded by the
    # two-space separator that joins the last count cell to it.
    assert "  (idle)" in rows[1]


def test_truncate_visible_plain_mode_emits_no_sgr():
    """Regression guard: when colorize=False, `_truncate_visible` must
    not inject `\\x1b[0m` into otherwise-plain output."""
    from ansible_aom.compact.renderer import _truncate_visible

    truncated = _truncate_visible("hello world", 5, colorize=False)
    assert "\x1b" not in truncated, repr(truncated)
    assert truncated.endswith("…")

    # Colorize=True keeps the RESET suffix to close any open SGR state.
    truncated_color = _truncate_visible("\x1b[31mhello world\x1b[0m", 5, colorize=True)
    assert truncated_color.endswith("\x1b[0m")


def test_format_tree_block_emits_tree_shape():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy webservers"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web2",
        },
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=20, width=80, ascii_mode=False, colorize=False)
    # block is list[str], one per line
    joined = "\n".join(block)
    assert "site.yml" in joined
    assert "play: deploy webservers" in joined
    assert "Install nginx" in joined
    assert "web1" in joined and "web2" in joined
    # Branch glyphs present
    assert "└─" in joined or "├─" in joined


def test_format_tree_block_ascii_fallback():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        },
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=20, width=80, ascii_mode=True, colorize=False)
    joined = "\n".join(block)
    # No Unicode glyphs in ascii mode
    for ch in ("└", "├", "─", "◐", "●", "◆"):
        assert ch not in joined, f"ascii mode contained {ch!r}"
    # ASCII branch markers used instead
    assert "+-" in joined or "\\-" in joined


def test_format_tree_block_invisible_returns_empty():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
    )
    p = TreeProjection.from_run_state(state)
    assert format_tree_block(p, budget=20, width=80, ascii_mode=False, colorize=False) == []


def test_format_tree_block_host_leaves_are_plain_indented():
    """Regression guard: host children render WITHOUT a branch glyph,
    matching the user-approved spec preview (`   web1 ◐ 12s`, not
    `├─ web1 ◐ 12s`)."""
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web2",
        },
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=20, width=80, ascii_mode=False, colorize=False)
    host_lines = [ln for ln in block if "web1" in ln or "web2" in ln]
    assert len(host_lines) == 2
    for hl in host_lines:
        # No branch glyph at the start (in either Unicode or ASCII form).
        # The hostname appears after pure whitespace indent.
        stripped = hl.lstrip()
        assert stripped.startswith(("web1", "web2")), (
            f"host line should begin with hostname after indent, got {hl!r}"
        )
        assert "├─" not in hl and "└─" not in hl, (
            f"host line should have no branch glyph, got {hl!r}"
        )


# =============================================================================
# Task 8: CompactRenderer integration — _render_status_panel composes
# status bar + tree + host rows into one Display update.
# =============================================================================


import shutil  # noqa: E402
from unittest.mock import patch  # noqa: E402

from ansible_aom.compact.renderer import CompactRenderer  # noqa: E402


def test_render_status_panel_is_status_bar_only_before_any_task():
    """When no task is RUNNING, the panel shows only the status bar —
    no tree, no host rows. We capture the assembled panel via the
    Display.update call rather than parsing stdout directly."""
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    assert m.called
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    assert "└─" not in content and "├─" not in content
    assert "on: " not in content


def test_render_status_panel_includes_tree_when_task_running(
    event_playbook_start, event_play_start, event_task_start, event_runner_start
):
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    r.update_state(event_playbook_start)
    r.update_state(event_play_start)
    r.update_state(event_task_start)
    r.update_state(event_runner_start)
    # Bypass the compute-throttle (HS-1/HS-8) so this direct render
    # always fires — without this the burst above already used up the
    # window and the spied update would never see a call.
    r._last_panel_compute_time = 0.0
    r._panel_dirty = True
    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    assert "Install nginx" in content
    assert "site.yml" in content


def test_hosts_completed_doesnt_oscillate_with_in_flight_task():
    """A host that previously reported OK and is now in the middle of
    the next task (status=RUNNING for that next task) should still
    count as 'completed' for the hosts-completed segment of the status
    bar — its OK status from the prior task is the meaningful signal,
    not the transient RUNNING for the in-flight one. Regression guard
    for: user reported the hosts count oscillating 0/1 during execution
    and 1/1 between tasks."""
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    assert r._state is not None
    # web1 completed task 1, then started task 2 (still running).
    play = r._state.plays.setdefault(
        "p1",
        __import__("ansible_aom.core.models", fromlist=["PlayRunState"]).PlayRunState(
            play_id="p1",
            name="deploy",
        ),
    )
    from ansible_aom.core.models import HostRunState, TaskRunState

    t1 = TaskRunState(task_id="t1", name="Install nginx")
    t1.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
    t2 = TaskRunState(task_id="t2", name="Configure firewall")
    t2.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t1"] = t1
    play.tasks["t2"] = t2

    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    # Status bar should show 1/1 hosts (web1 has terminal OK from t1),
    # NOT 0/1 (which would mean we're treating the RUNNING on t2 as
    # 'not done').
    assert "1/1 hosts" in content, f"expected '1/1 hosts', got: {content!r}"


def test_render_status_panel_status_bar_is_last_line(
    event_playbook_start, event_play_start, event_task_start, event_runner_start
):
    """The status bar must be the BOTTOM line of the panel so it stays
    anchored at the terminal's bottom. Tree + host rows render above it.
    Regression guard for: user reported the tree appeared BELOW the
    status line, which pushes the 'sticky' status bar off the natural
    bottom position."""
    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    r.update_state(event_playbook_start)
    r.update_state(event_play_start)
    r.update_state(event_task_start)
    r.update_state(event_runner_start)
    # Bypass the compute-throttle (HS-1/HS-8) — see sibling test.
    r._last_panel_compute_time = 0.0
    r._panel_dirty = True
    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    lines = content.splitlines()
    # Status bar carries the playbook name and elapsed time; tree carries
    # the play / task / host glyphs. Status bar must be the last line.
    assert any("site.yml" in ln for ln in lines), "expected playbook name somewhere"
    # The line containing "Install nginx" (a task or host leaf) must come
    # BEFORE the status bar's elapsed-time / playbook-name line.
    status_idx = next(i for i, ln in enumerate(lines) if "│" in ln and "site.yml" in ln)
    tree_lines = [i for i, ln in enumerate(lines) if "Install nginx" in ln]
    assert tree_lines, "tree content missing from panel"
    for ti in tree_lines:
        assert ti < status_idx, (
            f"tree line {ti} ({lines[ti]!r}) must come before status bar "
            f"at line {status_idx} ({lines[status_idx]!r})"
        )


def test_compute_tree_budget_math():
    from ansible_aom.compact.renderer import _compute_tree_budget

    # Baseline: 24 rows, 0 active hosts → 24//2 = 12
    assert _compute_tree_budget(rows=24, active_hosts=0) == 12
    # Host scaling: 24 rows, 12 active hosts → 12 + 4 = 16
    assert _compute_tree_budget(rows=24, active_hosts=12) == 16
    # Lower clamp: tiny terminal, 0 hosts → 8
    assert _compute_tree_budget(rows=10, active_hosts=0) == 8
    # Upper clamp: huge values → 60
    assert _compute_tree_budget(rows=200, active_hosts=200) == 60


def _full_panel(state: RunState) -> str:
    """Helper: render the assembled panel against a fixed 80-col terminal,
    24-row baseline. Returns the joined panel string (tree + host rows
    only; status bar is not part of these snapshots since it's a separate
    concern with its own dedicated tests)."""
    from ansible_aom.compact.renderer import (
        _compute_tree_budget,
        format_host_rows,
        format_tree_block,
    )

    p = TreeProjection.from_run_state(state)
    active = sum(
        1
        for play in state.plays.values()
        for task in play.tasks.values()
        for hs in task.hosts.values()
        if hs.status == Status.RUNNING
    )
    budget = _compute_tree_budget(24, active)
    tree = format_tree_block(p, budget=budget, width=80, ascii_mode=False, colorize=False)
    rows = (
        format_host_rows(p, width=80, ascii_mode=False, colorize=False)
        if p.is_host_summary_visible()
        else []
    )
    return "\n".join(tree + rows)


def test_linear_strategy_panel_shape():
    """One task running on three hosts — classic linear-strategy shape.
    Expect: one task line in the tree + three host children + three
    host rows below (one per host, each with `on: Install nginx`)."""
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        *[
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": h,
            }
            for h in ("web1", "web2", "web3")
        ],
    )
    panel = _full_panel(state)
    # Task line appears once; each host appears at least twice (tree leaf + host row).
    assert "Install nginx" in panel
    for h in ("web1", "web2", "web3"):
        assert panel.count(h) == 2, (
            f"expected {h!r} in both tree leaf and host row, got panel:\n{panel}"
        )


def test_free_strategy_panel_shows_two_tasks():
    """Free strategy: web1 on task A, web2 on task B simultaneously.
    Expect: two task lines in the tree with their respective host
    children, plus host rows showing divergent `on:` suffixes."""
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "host": "web1",
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "t2", "name": "Configure firewall"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t2", "name": "Configure firewall"},
            "host": "web2",
        },
    )
    panel = _full_panel(state)
    assert "Install nginx" in panel
    assert "Configure firewall" in panel
    # The host table's "on" column shows each host's current task name.
    # No "on:" prefix anymore — the column header carries that semantic.
    assert "web1" in panel
    assert "web2" in panel


def test_post_recap_panel_drops_tree_and_suffix():
    """After PLAY RECAP (`v2_playbook_on_stats`) no task is RUNNING, so
    the tree disappears entirely. Host rows remain but their suffix
    becomes `(idle)` (or is suppressed once the renderer detects the
    finished state)."""
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "deploy"},
        },
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "hosts": {"web2": {"ok": True, "changed": False}},
        },
        {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:00:10Z",
            "stats": {},
        },
    )
    panel = _full_panel(state)
    # Tree is gone (no branch glyphs at all).
    assert "└─" not in panel
    assert "├─" not in panel
    # Host rows still present.
    assert "web1" in panel and "web2" in panel
    # No `on: <task>` suffix — both hosts are idle.
    assert "on: " not in panel
    # Pin the observed shape: header row + two host rows with "(idle)".
    assert panel.count("(idle)") == 2
    assert len(panel.splitlines()) == 3


# =============================================================================
# Task 4 (two-level truncation renderer): the data layer (T1+T2+T3) emits
# `kind="more"` footers and `has_tail_after=True` markers. The renderer must
# honour both: footers hang off the spine without their own `├─`/`└─` glyph,
# and `has_tail_after=True` lines demote their branch glyph from `└─` to `├─`
# so the parent spine (`│  `) extends all the way down to the outer footer.
#
# These tests pin the renderer's contract about the *shape* of the input
# `TreeLine[]` it receives, so we monkeypatch `TreeProjection.tree_lines` to
# return hand-built lines rather than going through `_tree_lines_unbounded` /
# `_truncate_two_level`. That keeps the renderer tests focused on what T4
# actually owns: glyph emission for `kind="more"` and `has_tail_after`.
# =============================================================================


def _visible_projection(monkeypatch) -> TreeProjection:
    """Build a ``TreeProjection`` whose ``is_tree_visible()`` returns True
    and whose ``tree_lines()`` is monkeypatched to a callable the test can
    replace per-call. Minimal ``RunState`` so the visibility check passes.
    """
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="p1", name="deploy")
    task = TaskRunState(task_id="t1", name="Install nginx")
    task.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
    play.tasks["t1"] = task
    state.plays["p1"] = play
    projection = TreeProjection.from_run_state(state)

    lines_holder: list[TreeLine] = []

    def _stub(budget: int) -> list[TreeLine]:
        return lines_holder

    monkeypatch.setattr(projection, "tree_lines", _stub)
    # Stash the holder on the projection so individual tests can replace it.
    projection._t4_lines_holder = lines_holder  # type: ignore[attr-defined]
    return projection


def test_more_kind_suppresses_branch_glyph(monkeypatch) -> None:
    """A ``kind="more"`` line renders with an empty branch glyph — no
    ``├─`` or ``└─``. The footer hangs off the spine as a leaf.

    Constructed by hand: a normal task at depth 2 followed by a
    ``kind="more"`` footer at the same depth. Pre-T4 the renderer's
    branch-glyph selection treats ``"more"`` as an unknown kind, so it
    falls into the ``else`` branch and renders ``├─``/``└─`` like any
    other leaf. T4 adds ``"more"`` to the no-glyph special-case set.
    """
    projection = _visible_projection(monkeypatch)
    projection._t4_lines_holder.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: deploy",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="Install nginx",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=2,
                kind="more",
                label="… and 5 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=False, colorize=False)
    # The "more" line must not start with ├─ or └─. Its branch slot is empty,
    # so the line begins with indent + glyph ("□ ") + label.
    more_line = next(ln for ln in block if "more tasks" in ln)
    assert "├─" not in more_line, f"more footer must not have ├─ prefix; got {more_line!r}"
    assert "└─" not in more_line, f"more footer must not have └─ prefix; got {more_line!r}"
    # The PENDING icon □ renders so the footer reads as metadata-shaped.
    assert "□" in more_line, f"expected PENDING icon □ on more footer; got {more_line!r}"


def test_has_tail_after_demotes_last_to_mid(monkeypatch) -> None:
    """A line with ``has_tail_after=True`` draws ``├─`` instead of ``└─``.

    Without T4's look-ahead, a true last child renders ``└─``; with
    ``has_tail_after=True`` the renderer treats the line as having a
    sibling/descendant below, so the branch flips to ``├─`` and the
    parent spine continues.
    """
    projection = _visible_projection(monkeypatch)
    projection._t4_lines_holder.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: deploy",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="First task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="Second task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=False, colorize=False)
    first_task = next(ln for ln in block if "First task" in ln)
    # The first task is NOT the last child (a footer / sibling follows),
    # so its branch is ├─, not └─.
    assert "├─" in first_task, f"expected ├─ prefix on has_tail_after=True line; got {first_task!r}"
    assert "└─" not in first_task, f"└─ would indicate last-child; got {first_task!r}"


def test_ancestor_spine_continues_under_tail_after(monkeypatch) -> None:
    """The ancestor of a ``has_tail_after=True`` line draws ``│  `` in
    its indent chain — proving the spine continues through the cut.

    Four-level tree: playbook (d0) → play (d1, has_tail_after=True) →
    task (d2). The play is marked ``has_tail_after=True`` because it
    is the last visible line of the head (T2's truncation logic sets
    the same flag on the line just before the cut). With T4's
    ``is_last`` override, the play's branch flips from ``└─`` to
    ``├─``, and its descendant at depth 2 picks up ``│  `` from
    ``_ancestor_chain_indent`` instead of ``   `` — the spine
    extends from the playbook root down to the cut line.
    """
    projection = _visible_projection(monkeypatch)
    projection._t4_lines_holder.extend(  # type: ignore[attr-defined]
        [
            TreeLine(
                depth=0,
                kind="playbook",
                label="site.yml",
                glyph=None,
                status=None,
                elapsed_s=None,
            ),
            TreeLine(
                depth=1,
                kind="play",
                label="play: deploy",
                glyph=None,
                status=Status.RUNNING,
                elapsed_s=None,
                has_tail_after=True,
            ),
            TreeLine(
                depth=2,
                kind="task",
                label="Final visible task",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
            TreeLine(
                depth=0,
                kind="more",
                label="… and 5 more tasks",
                glyph=None,
                status=Status.PENDING,
                elapsed_s=None,
            ),
        ]
    )
    block = format_tree_block(projection, budget=10, width=80, ascii_mode=False, colorize=False)
    play_line = next(ln for ln in block if "play: deploy" in ln)
    task_line = next(ln for ln in block if "Final visible task" in ln)
    # The play has has_tail_after=True, so its branch flips to ├─.
    assert play_line.startswith("├─"), f"expected play to start with ├─; got {play_line!r}"
    # The task line at depth 2 has the play as its only ancestor. The
    # play is non-last (has_tail_after=True), so its ancestor segment
    # must be the vertical pipe `│  `.
    assert task_line.startswith("│  "), (
        f"ancestor spine must continue under has_tail_after=True; "
        f"expected `│  ├─` prefix on task; got {task_line!r}"
    )


def test_format_tree_block_renders_two_level_truncation(monkeypatch) -> None:
    """End-to-end snapshot of the user's sketch shape. Two plays,
    second with a ``podman`` role containing 33 tasks. With
    ``budget=15`` the truncation algorithm (T2) emits an inner footer
    at the role's task depth. The podman role footer claims all 30
    hidden tasks, so the outer footer is dropped (own-only contract:
    each hidden task is counted in exactly one footer, and no play
    footer is emitted). The footer must render with the PENDING icon
    and no branch glyph, and the line immediately above it must render
    with ``├─`` (the spur that keeps the spine connected to the
    footer).
    """
    from ansible_aom.core.models import PlayDefinition, RoleGroupDefinition, TaskDefinition

    # Build the state DIRECTLY (rather than replaying events) so both
    # plays are visible to the active-play logic in
    # ``_tree_lines_unbounded``. Event replay's force-finalisation
    # rules hide the previous play once a later play starts — we
    # want both visible for the multi-play shape the user's sketch
    # describes.
    state = RunState(playbook="smfc-and-scrutiny.yml")
    state.definitions = [
        PlayDefinition(
            id="p1",
            name="Supermicro Fan Control (smfc) Install and Config",
            hosts="localhost",
            resolved_hosts=["host1"],
            tasks=[
                RoleGroupDefinition(
                    role="smfc",
                    tasks=[
                        TaskDefinition(
                            name=f"smfc : step {i}",
                            role="smfc",
                            tags=[],
                            play_id="p1",
                            play_order=0,
                            task_order=i,
                        )
                        for i in range(3)
                    ],
                )
            ],
        ),
        PlayDefinition(
            id="p2",
            name="Setup rootless Podman for Scrutiny web server",
            hosts="localhost",
            resolved_hosts=["host1"],
            tasks=[
                RoleGroupDefinition(
                    role="podman",
                    tasks=[
                        TaskDefinition(
                            name=f"podman : Podman task {i}",
                            role="podman",
                            tags=[],
                            play_id="p2",
                            play_order=1,
                            task_order=i,
                        )
                        for i in range(33)
                    ],
                )
            ],
        ),
    ]
    # Runtime: one task per play running. Play 1 has 1 RUNNING, play 2
    # has 1 RUNNING on host1. Both plays therefore contribute to the
    # active-play filter, and the unbounded tree holds both plays.
    from ansible_aom.core.models import HostRunState, PlayRunState, TaskRunState

    p1 = PlayRunState(play_id="p1", name="Supermicro Fan Control (smfc) Install and Config")
    t_p1 = TaskRunState(task_id="smfc_t0", name="smfc : step 0", status=Status.RUNNING)
    t_p1.hosts["host1"] = HostRunState(hostname="host1", status=Status.RUNNING)
    p1.tasks["smfc_t0"] = t_p1
    state.plays["p1"] = p1

    p2 = PlayRunState(play_id="p2", name="Setup rootless Podman for Scrutiny web server")
    t_p2 = TaskRunState(task_id="podman_t0", name="podman : Podman task 0", status=Status.RUNNING)
    t_p2.hosts["host1"] = HostRunState(hostname="host1", status=Status.RUNNING)
    p2.tasks["podman_t0"] = t_p2
    state.plays["p2"] = p2

    projection = TreeProjection.from_run_state(state)
    # Sanity: the unbounded tree must exceed budget so T2 kicks in.
    unbounded = projection.tree_lines(budget=200)
    assert len(unbounded) > 10, (
        f"test fixture must overflow budget=10 for T2 to engage; got {len(unbounded)} lines"
    )

    block = format_tree_block(projection, budget=15, width=120, ascii_mode=False, colorize=False)
    joined = "\n".join(block)

    # All footers (role + outer) must render. The podman role footer
    # claims all 30 hidden tasks, so the outer footer is dropped.
    more_lines = [ln for ln in block if "more tasks" in ln]
    assert len(more_lines) == 1, (
        f"expected exactly 1 'more tasks' footer (role only, outer dropped); got {len(more_lines)} in:\n{joined}"
    )
    # The footer carries the PENDING icon □ (T4 Edit 3) and has no
    # branch glyph (T4 Edit 1).
    for footer in more_lines:
        assert "□" in footer, f"every 'more' footer must carry the PENDING icon; got {footer!r}"
        assert "├─" not in footer and "└─" not in footer, (
            f"footers must have no branch glyph; got {footer!r}"
        )

    # The role label reads "(N tasks)" (the role's total) inside the
    # cut — never "(M remaining)" (T3 suffix-drop contract).
    role_line = next(ln for ln in block if "podman" in ln and "role" in ln.lower())
    assert "remaining" not in role_line, (
        f"role label must NOT carry '(M remaining)' suffix; got {role_line!r}"
    )
    # And it must carry the "(N tasks)" count form. The podman role in
    # this fixture has 33 subtree tasks.
    assert "(33 tasks)" in role_line, (
        f"role label must carry '(N tasks)' count form; got {role_line!r}"
    )

    # Every non-host, non-root line in the inner section (the cut
    # starts at the second play: "Setup rootless Podman...") must draw
    # ├─ (the has_tail_after spur) so the spine extends from the top
    # of the cut window down to the inner footer. Host leaves and
    # the playbook root are excluded (no branch glyph of their own).
    #
    # Pre-fix this fails on the second play, the podman role, and the
    # visible tasks — they all rendered as └─ because T2 only marked
    # the last line of the inner section. Post-fix (marking every line
    # in the inner section) every non-leaf line in the cut carries ├─.
    inner_footer_idx = next(i for i, ln in enumerate(block) if "and 30 more tasks" in ln)
    # Find the cut start: the second play line "Setup rootless Podman".
    cut_start_idx = next(i for i, ln in enumerate(block) if "Setup rootless Podman" in ln)
    for i in range(cut_start_idx, inner_footer_idx):
        line = block[i]
        if "host1 ◐" in line or "h1 ◐" in line:
            # Host leaves: no own branch glyph, but the indent prefix
            # carries the running spine.
            continue
        # Every non-host line in the inner section must draw ├─.
        assert "├─" in line, (
            f"line {i} in the inner section must draw ├─ (has_tail_after spur); got {line!r}"
        )
