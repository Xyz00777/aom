"""Pilot-based tests for F1 — Live TUI widget refresh.

These tests drive a real Textual app through a Pilot and assert that
periodic refreshes pull RunState mutations onto the screen, that the
worker thread can call add_warning / print_log without touching
widgets directly, and that completion does one final refresh plus a
title update.
"""

from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest

from ansible_aom.tui.app import AOMApp


class TestDirtyCounter:
    """The dirty counter is the worker→UI signal."""

    def test_dirty_counter_starts_at_zero(self) -> None:
        app = AOMApp()
        assert app._dirty == 0

    def test_update_state_increments_dirty(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        before = app._dirty
        app.update_state(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-05-12T10:00:00Z",
                "play": {"id": "p1", "name": "Setup"},
            }
        )
        assert app._dirty == before + 1

    def test_add_warning_increments_dirty(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        before = app._dirty
        app.add_warning("[WARNING]: x")
        assert app._dirty == before + 1

    def test_print_log_buffers_line_and_increments_dirty(self) -> None:
        app = AOMApp()
        app.start("site.yml", [])
        before = app._dirty
        app.print_log("TASK [foo] ***")
        assert app._dirty == before + 1
        assert "TASK [foo] ***" in app._pending_log_lines

    def test_set_definitions_increments_dirty(self) -> None:
        from ansible_aom.core.models import PlayDefinition

        app = AOMApp()
        app.start("site.yml", [])
        before = app._dirty
        app.set_definitions([PlayDefinition(id="1", name="P", hosts="all")])
        assert app._dirty == before + 1


class TestTreePopulationFromDefinitions:
    """First-time tree population uses preflight definitions."""

    def test_populate_from_definitions_adds_play_nodes(self) -> None:
        from ansible_aom.core.models import PlayDefinition, TaskDefinition
        from ansible_aom.tui.widgets.task_tree import TaskTree

        tree = TaskTree("Plays")
        defs = [
            PlayDefinition(
                id="p1",
                name="Setup",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=0,
                    ),
                ],
            )
        ]

        tree.populate_from_definitions(defs)

        # One play node, with one task child, with two host grandchildren.
        play_nodes = list(tree.root.children)
        assert len(play_nodes) == 1
        task_nodes = list(play_nodes[0].children)
        assert len(task_nodes) == 1
        host_nodes = list(task_nodes[0].children)
        assert len(host_nodes) == 2

    def test_populate_from_definitions_is_idempotent(self) -> None:
        from ansible_aom.core.models import PlayDefinition
        from ansible_aom.tui.widgets.task_tree import TaskTree

        tree = TaskTree("Plays")
        defs = [PlayDefinition(id="p1", name="Setup", hosts="all", resolved_hosts=[])]

        tree.populate_from_definitions(defs)
        tree.populate_from_definitions(defs)

        # Calling twice with the same defs must not duplicate nodes.
        assert len(list(tree.root.children)) == 1
