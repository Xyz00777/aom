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
