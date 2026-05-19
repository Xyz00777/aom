"""Snapshot tests for the compact renderer's tree + host-row block.

These pin the rendered text shape. Updates require explicit golden
changes — adjust the expected strings when you intentionally change
formatting, not when you accidentally do.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import format_host_rows, format_tree_block
from ansible_aom.core.models import RunState, Status
from ansible_aom.core.tree import TreeProjection


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
    assert len(rows) == 1
    assert "web1" in rows[0]
    assert "on: Install nginx" in rows[0]
    assert "◐" in rows[0]


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
    assert "(idle)" in rows[0]
    assert "● 1 ok" in rows[0]


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
    assert "unreachable" in rows[0]
    assert "⊝ 1" in rows[0]


def test_format_host_rows_uses_two_space_gap_between_cells_and_suffix():
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
    # Cells: "● 1 ok"  Suffix: "(idle)"  ⇒  expect "...● 1 ok  (idle)"
    assert "● 1 ok  (idle)" in rows[0]
    # Triple-space should NOT appear anywhere in the rendered row.
    assert "   " not in rows[0]


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
    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    assert "Install nginx" in content
    assert "site.yml" in content


def test_compute_tree_budget_math():
    from ansible_aom.compact.renderer import _compute_tree_budget
    # Baseline: 24 rows, 0 active hosts → 24//3 = 8
    assert _compute_tree_budget(rows=24, active_hosts=0) == 8
    # Host scaling: 24 rows, 12 active hosts → 8 + 4 = 12
    assert _compute_tree_budget(rows=24, active_hosts=12) == 12
    # Lower clamp: tiny terminal, 0 hosts → 5
    assert _compute_tree_budget(rows=10, active_hosts=0) == 5
    # Upper clamp: huge values → 25
    assert _compute_tree_budget(rows=200, active_hosts=200) == 25


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
    tree = format_tree_block(
        p, budget=budget, width=80, ascii_mode=False, colorize=False
    )
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
    # Per-host row suffixes show divergent current tasks.
    assert "web1" in panel and "on: Install nginx" in panel
    assert "web2" in panel and "on: Configure firewall" in panel


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
    # Pin the observed shape: two host rows with "(idle)" suffix.
    assert panel.count("(idle)") == 2
    assert len(panel.splitlines()) == 2
