"""Snapshot tests for the compact renderer's tree + host-row block.

These pin the rendered text shape. Updates require explicit golden
changes — adjust the expected strings when you intentionally change
formatting, not when you accidentally do.
"""
from __future__ import annotations

from ansible_aom.compact.renderer import format_host_rows
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
        {"_event": "v2_playbook_on_play_start",
         "_timestamp": "2026-04-20T10:00:01Z",
         "play": {"id": "p1", "name": "deploy"}},
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:02Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "play": {"id": "p1"}},
        {"_event": "v2_runner_on_start",
         "_timestamp": "2026-04-20T10:00:03Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "host": "web1"},
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
        {"_event": "v2_playbook_on_play_start",
         "_timestamp": "2026-04-20T10:00:01Z",
         "play": {"id": "p1", "name": "deploy"}},
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:02Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "play": {"id": "p1"}},
        {"_event": "v2_runner_on_ok",
         "_timestamp": "2026-04-20T10:00:05Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "hosts": {"web1": {"ok": True, "changed": False}}},
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    assert "(idle)" in rows[0]
    assert "● 1 ok" in rows[0]


def test_format_host_rows_unreachable_host_shows_unreachable():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {"_event": "v2_playbook_on_play_start",
         "_timestamp": "2026-04-20T10:00:01Z",
         "play": {"id": "p1", "name": "deploy"}},
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:02Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "play": {"id": "p1"}},
        {"_event": "v2_runner_on_unreachable",
         "_timestamp": "2026-04-20T10:00:05Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "hosts": {"db1": {"unreachable": True}}},
    )
    p = TreeProjection.from_run_state(state)
    rows = format_host_rows(p, width=80, ascii_mode=False, colorize=False)
    assert "unreachable" in rows[0]
    assert "⊝ 1" in rows[0]
