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


class TestApplyStateIcons:
    """apply_state_icons updates icons/colors without rebuilding nodes."""

    def test_apply_state_icons_updates_task_icon(self) -> None:
        from ansible_aom.core.models import (
            HostRunState,
            PlayDefinition,
            PlayRunState,
            RunState,
            Status,
            TaskDefinition,
            TaskRunState,
        )
        from ansible_aom.tui.widgets.task_tree import TaskTree

        tree = TaskTree("Plays")
        tree.populate_from_definitions(
            [
                PlayDefinition(
                    id="p1",
                    name="Setup",
                    hosts="webservers",
                    resolved_hosts=["web1"],
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
        )

        # Snapshot the original task node so we can prove identity is
        # preserved (the same TreeNode instance, not a fresh one).
        play_node = list(tree.root.children)[0]
        task_node_before = list(play_node.children)[0]
        original_id = id(task_node_before)

        # Build a RunState with the task marked OK.
        state = RunState(playbook="site.yml")
        play = PlayRunState(play_id="p1", name="Setup")
        task = TaskRunState(task_id="t1", name="Install nginx", status=Status.OK)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        play.tasks["t1"] = task
        state.plays["p1"] = play

        tree.apply_state_icons(state)

        task_node_after = list(play_node.children)[0]
        assert id(task_node_after) == original_id  # same node, mutated label
        # The OK icon (●) must now be in the rendered label text.
        from ansible_aom.core.icons import STATUS_ICONS

        ok_icon = STATUS_ICONS[Status.OK]
        assert ok_icon in task_node_after.label.plain

    def test_apply_state_icons_updates_host_icon(self) -> None:
        from ansible_aom.core.icons import STATUS_ICONS
        from ansible_aom.core.models import (
            HostRunState,
            PlayDefinition,
            PlayRunState,
            RunState,
            Status,
            TaskDefinition,
            TaskRunState,
        )
        from ansible_aom.tui.widgets.task_tree import TaskTree

        tree = TaskTree("Plays")
        tree.populate_from_definitions(
            [
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
        )

        state = RunState(playbook="site.yml")
        play = PlayRunState(play_id="p1", name="Setup")
        task = TaskRunState(task_id="t1", name="Install nginx", status=Status.RUNNING)
        task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
        task.hosts["web2"] = HostRunState(hostname="web2", status=Status.FAILED)
        play.tasks["t1"] = task
        state.plays["p1"] = play

        tree.apply_state_icons(state)

        play_node = list(tree.root.children)[0]
        task_node = list(play_node.children)[0]
        host_nodes = list(task_node.children)
        # web1 should show OK, web2 FAILED.
        labels = {n.data: n.label.plain for n in host_nodes}
        assert STATUS_ICONS[Status.OK] in labels["host:web1"]
        assert STATUS_ICONS[Status.FAILED] in labels["host:web2"]


class TestMainScreenTreeIntegration:
    """update_from_state plumbs RunState through to TaskTree."""

    @pytest.mark.asyncio
    async def test_update_from_state_populates_tree_from_definitions(self) -> None:
        from ansible_aom.core.models import PlayDefinition, TaskDefinition
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        app = AOMApp()

        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            screen = app.screen
            assert isinstance(screen, MainScreen)

            app.run_state.definitions = [
                PlayDefinition(
                    id="p1",
                    name="Setup",
                    hosts="all",
                    resolved_hosts=["web1"],
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
            screen.update_from_state(app.run_state)
            await pilot.pause(0.05)

            tree = screen.query_one(TaskTree)
            assert len(list(tree.root.children)) == 1

    @pytest.mark.asyncio
    async def test_update_from_state_drops_completed_tasks(self) -> None:
        """All-completed tasks must NOT remain visible in the tree.

        Regression for: ``apply_state_icons`` only mutated labels in
        place, so completed tasks built from the preflight skeleton
        stayed in the tree forever. The fix wires
        ``populate_from_projection`` into the refresh path, which
        rebuilds the tree from ``TreeProjection.tree_lines`` — that
        path drops completed tasks via ``_play_running_and_pending``.
        """
        from ansible_aom.core.models import (
            HostRunState,
            PlayDefinition,
            PlayRunState,
            RunState,
            Status,
            TaskDefinition,
            TaskRunState,
        )
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            screen = app.screen
            assert isinstance(screen, MainScreen)

            app.run_state.definitions = [
                PlayDefinition(
                    id="p1",
                    name="Setup",
                    hosts="all",
                    resolved_hosts=["web1"],
                    tasks=[
                        TaskDefinition(
                            name=f"Task {i}",
                            role=None,
                            tags=[],
                            play_id="p1",
                            play_order=0,
                            task_order=i,
                        )
                        for i in range(3)
                    ],
                )
            ]
            play = PlayRunState(play_id="p1", name="Setup")
            for i, name in enumerate(["Task 0", "Task 1", "Task 2"]):
                task = TaskRunState(task_id=f"t{i}", name=name, status=Status.COMPLETED)
                task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
                play.tasks[f"t{i}"] = task
            app.run_state.plays["p1"] = play

            screen.update_from_state(app.run_state)
            await pilot.pause(0.05)

            tree = screen.query_one(TaskTree)
            play_nodes = list(tree.root.children)
            assert play_nodes == [], (
                f"all-completed play must not appear in the tree; "
                f"got {[p.label.plain for p in play_nodes]}"
            )

    @pytest.mark.asyncio
    async def test_update_from_state_keeps_running_task_visible(self) -> None:
        """Mixed scenario: completed tasks drop, running task remains.

        Regression for the projection-based refresh: a play with both
        completed and running tasks must show ONLY the running task's
        subtree plus any pending preflight tasks — not the completed
        history.
        """
        from datetime import datetime, timezone

        from ansible_aom.core.models import (
            HostRunState,
            PlayDefinition,
            PlayRunState,
            RunState,
            Status,
            TaskDefinition,
            TaskRunState,
        )
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            screen = app.screen
            assert isinstance(screen, MainScreen)

            app.run_state.definitions = [
                PlayDefinition(
                    id="p1",
                    name="Setup",
                    hosts="all",
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
                        TaskDefinition(
                            name="Configure nginx",
                            role=None,
                            tags=[],
                            play_id="p1",
                            play_order=0,
                            task_order=1,
                        ),
                    ],
                )
            ]
            play = PlayRunState(play_id="p1", name="Setup")
            completed = TaskRunState(task_id="t0", name="Install nginx", status=Status.COMPLETED)
            completed.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
            completed.hosts["web2"] = HostRunState(hostname="web2", status=Status.OK)
            play.tasks["t0"] = completed

            running = TaskRunState(
                task_id="t1",
                name="Configure nginx",
                status=Status.RUNNING,
                start_time=datetime.now(timezone.utc),
            )
            running.hosts["web1"] = HostRunState(hostname="web1", status=Status.RUNNING)
            running.hosts["web2"] = HostRunState(hostname="web2", status=Status.RUNNING)
            play.tasks["t1"] = running

            app.run_state.plays["p1"] = play

            screen.update_from_state(app.run_state)
            await pilot.pause(0.05)

            tree = screen.query_one(TaskTree)
            play_nodes = list(tree.root.children)
            assert len(play_nodes) == 1, "active play must stay visible"
            task_labels = [t.label.plain for t in play_nodes[0].children]
            assert "Install nginx" not in " ".join(task_labels), (
                f"completed task must not appear; got {task_labels!r}"
            )
            assert any("Configure nginx" in lbl for lbl in task_labels), (
                f"running task must appear; got {task_labels!r}"
            )

    @pytest.mark.asyncio
    async def test_update_from_state_shows_ok_icon_after_completion(self) -> None:
        """After playbook completion, tasks must show their final status icon.

        Regression for: the projection-based rebuild path skipped
        ``apply_state_icons`` when ``is_tree_visible()`` returned False
        (because ``end_time`` is set). This caused the tree to fall back
        to ``populate_from_definitions`` which resets all icons to PENDING.
        The fix restores the two-step behaviour in the non-visible branch:
        skeleton built once, icons mutated every call.
        """
        from datetime import datetime, timezone

        from ansible_aom.core.icons import STATUS_ICONS
        from ansible_aom.core.models import (
            HostRunState,
            PlayDefinition,
            PlayRunState,
            RunState,
            Status,
            TaskDefinition,
            TaskRunState,
        )
        from ansible_aom.tui.app import AOMApp
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        app = AOMApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.05)
            screen = app.screen
            assert isinstance(screen, MainScreen)

            app.run_state.definitions = [
                PlayDefinition(
                    id="p1",
                    name="Setup",
                    hosts="all",
                    resolved_hosts=["web1"],
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
            play = PlayRunState(play_id="p1", name="Setup")
            task = TaskRunState(task_id="t0", name="Install nginx", status=Status.OK)
            task.hosts["web1"] = HostRunState(hostname="web1", status=Status.OK)
            play.tasks["t0"] = task
            app.run_state.plays["p1"] = play
            app.run_state.end_time = datetime.now(timezone.utc)

            screen.update_from_state(app.run_state)
            await pilot.pause(0.05)

            tree = screen.query_one(TaskTree)
            play_nodes = list(tree.root.children)
            assert len(play_nodes) == 1, "play must be visible after completion"
            task_nodes = list(play_nodes[0].children)
            assert len(task_nodes) == 1, "task must be visible after completion"
            ok_icon = STATUS_ICONS[Status.OK]
            task_label = task_nodes[0].label.plain
            assert ok_icon in task_label, (
                f"task must show OK icon after completion; got {task_label!r}, expected {ok_icon!r}"
            )


class TestPeriodicRefresh:
    """A 0.2s tick refreshes widgets when _dirty has advanced."""

    @pytest.mark.asyncio
    async def test_tick_refreshes_widgets_after_event(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        # Stub the runner so we can drive events directly.
        events_done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            from ansible_aom.core.models import PlayDefinition, TaskDefinition

            renderer.set_definitions(
                [
                    PlayDefinition(
                        id="p1",
                        name="Setup",
                        hosts="all",
                        resolved_hosts=["web1"],
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
            )
            renderer.update_state(
                {
                    "_event": "v2_playbook_on_play_start",
                    "_timestamp": "2026-05-12T10:00:00Z",
                    "play": {"id": "p1", "name": "Setup"},
                }
            )
            events_done.set()
            renderer.handle_completion(0, "completed")
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if events_done.is_set():
                    break
                await pilot.pause(0.02)
            # Wait for at least one refresh tick (>0.2s).
            await pilot.pause(0.4)

            screen = app.screen
            assert isinstance(screen, MainScreen)
            tree = screen.query_one(TaskTree)
            assert len(list(tree.root.children)) == 1, (
                "tree should have one play node after a refresh tick"
            )

    @pytest.mark.asyncio
    async def test_tick_drains_pending_log_lines(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        printed = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            renderer.print_log("TASK [Install nginx] ***")
            renderer.print_log("ok: [web1]")
            printed.set()
            renderer.handle_completion(0, "completed")
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if printed.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)
            # The pending buffer must be drained after the tick fires.
            assert app._pending_log_lines == []


class TestCallFromThreadRouting:
    """Worker-thread renderer callbacks marshal through the event loop."""

    @pytest.mark.asyncio
    async def test_add_warning_from_worker_lands_on_status_bar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        warned = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            renderer.add_warning("[WARNING]: missing role")
            renderer.add_warning("[DEPRECATION WARNING]: foo", is_deprecation=True)
            warned.set()
            renderer.handle_completion(0, "completed")
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if warned.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)

            assert app.warnings_count == 1
            assert app.deprecations_count == 1
            # The dirty counter must have advanced from the worker side
            # without the test having touched the app from the main
            # thread.
            assert app._dirty >= 2


class TestCompletionTitleUpdate:
    """handle_completion does one final refresh and updates the title."""

    @pytest.mark.asyncio
    async def test_completion_zero_marks_title_with_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            renderer.handle_completion(0, "completed")
            done.set()
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if done.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)

            assert "✓" in app.title

    @pytest.mark.asyncio
    async def test_completion_nonzero_marks_title_with_cross(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            renderer.handle_completion(2, "failed")
            done.set()
            return 2

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if done.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)

            assert "✖" in app.title


class TestEndToEndThreeTasks:
    """Projection-based refresh: only the currently running task is visible.

    Under linear strategy, each new task_start auto-completes the previous
    one. After three task_starts, only the last task (Task 2) remains
    RUNNING — the projection drops the two completed tasks from the tree.
    """

    @pytest.mark.asyncio
    async def test_three_task_starts_appear_in_tree(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from ansible_aom.core.models import PlayDefinition, TaskDefinition
        from ansible_aom.tui.screens.main import MainScreen
        from ansible_aom.tui.widgets.task_tree import TaskTree

        events_done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
            record: bool = True,
        ) -> int:
            renderer.start(playbook, ansible_args)
            renderer.set_definitions(
                [
                    PlayDefinition(
                        id="p1",
                        name="Setup",
                        hosts="all",
                        resolved_hosts=["web1"],
                        tasks=[
                            TaskDefinition(
                                name=f"Task {i}",
                                role=None,
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=i,
                            )
                            for i in range(3)
                        ],
                    )
                ]
            )
            renderer.update_state(
                {
                    "_event": "v2_playbook_on_play_start",
                    "_timestamp": "2026-05-12T10:00:00Z",
                    "play": {"id": "p1", "name": "Setup"},
                }
            )
            for i in range(3):
                renderer.update_state(
                    {
                        "_event": "v2_playbook_on_task_start",
                        "_timestamp": f"2026-05-12T10:00:0{i + 1}Z",
                        "task": {"id": f"t{i}", "name": f"Task {i}"},
                    }
                )
            events_done.set()
            renderer.handle_completion(0, "completed")
            return 0

        monkeypatch.setattr("ansible_aom.ansible.runner.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if events_done.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)

            screen = app.screen
            assert isinstance(screen, MainScreen)
            tree = screen.query_one(TaskTree)
            play_nodes = list(tree.root.children)
            assert len(play_nodes) == 1, "expected one play node"
            task_nodes = list(play_nodes[0].children)
            # Under linear strategy, Task 0 and Task 1 are auto-completed
            # when Task 2 starts. The projection drops completed tasks, so
            # only the running task (Task 2) remains visible.
            assert len(task_nodes) == 1, (
                f"expected 1 running task node, got {len(task_nodes)}: "
                f"{[n.label.plain for n in task_nodes]}"
            )
            assert "Task 2" in task_nodes[0].label.plain, (
                f"expected Task 2 label, got {task_nodes[0].label.plain}"
            )
