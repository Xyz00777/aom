# F1 — Live TUI Widget Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Textual TUI widgets (TaskTree, LogPanel, StatusBar, SummaryPanel) actually redraw on screen during a live `ansible-playbook` run by introducing a periodic refresh tick that drains a worker-set "dirty" counter.

**Architecture:** The pexpect runner already drives `AOMApp` from a Textual worker thread; `RunState` already mutates correctly. We add a single integer "dirty" counter on `AOMApp`. Renderer-Protocol callbacks (`update_state`, `add_warning`, `print_log`, `set_definitions`, `handle_completion`) increment the counter from the worker thread and use `call_from_thread` to schedule any actions that touch widgets directly (log line writes, tree first-population). On `on_mount`, the app installs a 0.2-second `set_interval` tick that, if the dirty counter has advanced since its last read, calls `MainScreen.update_from_state(self.run_state)` plus drains buffered log lines into `LogPanel`. `TaskTree` gains `populate_from_definitions(defs)` (first-time skeleton from preflight) and an idempotent `apply_state_icons(state)` (in-place icon/color updates). `handle_completion` triggers one final refresh and updates the app `title` with a ✓ / ✖ marker.

**Tech Stack:** Python 3.14, Textual ≥0.60 (`set_interval`, `call_from_thread`, `Tree.TreeNode.set_label`), Rich (`Text`), `threading` (no `Lock` — single-int reads/writes are GIL-safe), pytest-asyncio + Textual `Pilot`.

---

## File Structure

**Create:**
- `tests/tui/test_live_refresh.py` — Pilot-based integration tests for the periodic refresh, worker-thread safety of `add_warning` / `print_log`, tree first-population, in-place icon updates, and completion-time title change.

**Modify:**
- `src/ansible_aom/tui/app.py` (lines 14–292) — add a `_dirty` counter and a `_pending_log_lines` buffer; route worker-thread callbacks through `call_from_thread`; install the periodic refresh in `on_mount`; do a final refresh + title update inside `handle_completion`.
- `src/ansible_aom/tui/screens/main.py` (lines 67–110) — extend `update_from_state` to also call `TaskTree.populate_from_definitions` (once) and `TaskTree.apply_state_icons` (every tick); guard widget queries when the screen is not yet mounted.
- `src/ansible_aom/tui/widgets/task_tree.py` (lines 103–125) — add `populate_from_definitions(defs)` for the preflight skeleton plus `apply_state_icons(state)` for idempotent in-place icon/color updates. Keep `populate_from_state` for backward compatibility with existing tests.

**Do NOT modify:**
- `src/ansible_aom/core/state.py` / `core/models.py` — RunState already exposes everything we need.
- `src/ansible_aom/runner.py` — already calls renderer methods correctly.
- Existing `tests/tui/test_panels.py`, `tests/tui/test_tree_view.py`, `tests/tui/test_app_end_to_end.py` — must continue to pass unchanged.

**Risks called out (must be respected by the implementation):**

1. **Race between worker-thread writes and UI-tick reads of `_dirty`.** A plain `int` increment in CPython is *not* atomic at the bytecode level (`LOAD`/`ADD`/`STORE`), but the GIL serialises bytecode steps and the absolute counter value isn't load-bearing — we only check `current != last_seen`. A lost increment merely defers a refresh until the next genuine event arrives. Document this in a comment; do **not** add a Lock (it would block the worker on every event for no benefit).
2. **`set_interval` callbacks are async and can fire after a screen swap.** A `query_one` against a screen that isn't mounted raises. Guard with `if not self.screen.is_mounted: return` (note: `self.screen.is_mounted`, not `self.is_mounted` — the latter survives screen swaps but isn't what we want; we want to be sure the *current* screen has its widgets). Also wrap the body of the tick in a broad `except Exception` and log via `self.log.error(...)` so a transient widget-state hiccup doesn't kill the timer.

---

## Task 1: `_dirty` counter and pending log buffer on `AOMApp`

**Files:**
- Modify: `src/ansible_aom/tui/app.py:48-77` (constructor) and `tui/app.py:131-160` (callbacks)
- Test: `tests/tui/test_live_refresh.py` (new file)

The counter is the synchronisation point between the worker thread (writes) and the UI tick (reads). The pending-log buffer lets us defer `LogPanel.write_line` calls — which must happen on the UI thread — until the tick drains them.

- [ ] **Step 1: Write the failing test**

Create `tests/tui/test_live_refresh.py` with:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestDirtyCounter -v`
Expected: FAIL with `AttributeError: 'AOMApp' object has no attribute '_dirty'`.

- [ ] **Step 3: Implement the counter and buffer**

In `src/ansible_aom/tui/app.py`, modify the constructor (around line 66) to add the new fields. Replace the existing `__init__` body's tail:

```python
        super().__init__(**kwargs)
        self._playbook: str | None = playbook
        self._args: list[str] = list(ansible_args) if ansible_args is not None else []
        self._session_dir: Path | None = session_dir
        self._state: str = "IDLE"
        self._exit_code: int | None = None
        self._final_state: str | None = None
        self._run_state: RunState = RunState(playbook=playbook or "")
        self._warnings_count: int = 0
        self._deprecations_count: int = 0
        self._log_lines: list[str] = []
        # F1: worker→UI signalling. _dirty is incremented by every
        # renderer callback that mutates state; the periodic tick in
        # on_mount() refreshes widgets only when the value advances.
        # CPython int writes are not strictly atomic but the GIL
        # serialises bytecode and we only ever compare current vs last
        # seen — a lost increment defers, never corrupts.
        self._dirty: int = 0
        # Lines buffered by print_log() from the worker thread; the
        # UI tick drains these into LogPanel on the main thread (Rich
        # widgets are not thread-safe).
        self._pending_log_lines: list[str] = []
```

Then update each renderer callback to bump `_dirty` (and, for `print_log`, append to the pending buffer). Replace the existing four methods (around lines 127–160):

```python
    def set_definitions(self, definitions: list) -> None:
        """Renderer Protocol: store preflight definitions on the RunState."""
        self._run_state.definitions = list(definitions)
        self._dirty += 1

    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Renderer Protocol: bump counters; widgets can read them."""
        if is_deprecation:
            self._deprecations_count += 1
        else:
            self._warnings_count += 1
        self._dirty += 1

    def print_log(self, message: str) -> None:
        """Renderer Protocol: append a line to the log buffer.

        The line is also queued in ``_pending_log_lines`` so the periodic
        UI tick can write it into ``LogPanel`` on the main thread.
        """
        self._log_lines.append(message)
        self._pending_log_lines.append(message)
        self._dirty += 1
```

And modify `update_state` (around line 146) to bump the counter as its last action:

```python
    def update_state(self, event: dict) -> None:
        """Renderer Protocol: route the JSONL event through RunState.

        Called from the runner worker thread. The mutation itself is
        cheap and thread-safe on a plain dataclass; visible widget
        refreshes happen on the next periodic tick (see ``on_mount``).
        """
        self._run_state.handle_event(event)
        event_type = event.get("_event", "")
        if event_type == "v2_playbook_on_play_start":
            self._state = "RUNNING"
        elif event_type == "v2_playbook_on_stats":
            self._state = "COMPLETED"
        self._dirty += 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestDirtyCounter -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Run the full suite to confirm nothing broke**

Run: `uv run pytest tests/ -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/app.py tests/tui/test_live_refresh.py
git commit -m "feat(tui): add dirty counter and pending-log buffer for live refresh

Renderer-Protocol callbacks now bump a single int counter from the
worker thread; print_log additionally queues lines for the UI tick to
drain. Sets the foundation for the periodic refresh added in F1."
```

---

## Task 2: `populate_from_definitions` on `TaskTree`

**Files:**
- Modify: `src/ansible_aom/tui/widgets/task_tree.py:103-125`
- Test: `tests/tui/test_live_refresh.py`

The preflight phase delivers `set_definitions(defs)` *before* any JSONL events arrive. We want the tree to show all known plays/tasks/hosts as a skeleton (PENDING icons) so the user sees the run shape immediately, then status icons flip in place as events come through.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestTreePopulationFromDefinitions -v`
Expected: FAIL with `AttributeError: 'TaskTree' object has no attribute 'populate_from_definitions'`.

- [ ] **Step 3: Implement `populate_from_definitions` and `apply_state_icons`**

In `src/ansible_aom/tui/widgets/task_tree.py`, after the existing `populate_from_state` method (around line 125), add:

```python
    def populate_from_definitions(self, definitions: list) -> None:
        """Build the initial tree skeleton from preflight definitions.

        Called once when ``set_definitions`` first lands. Subsequent
        state changes go through ``apply_state_icons`` which mutates
        node labels in place rather than rebuilding the tree.

        Idempotent: clears existing children first so a double-call
        (e.g. preflight retried) produces the same tree.
        """
        from ansible_aom.core.models import RoleGroupDefinition, TaskDefinition

        self.root.remove_children()

        for play_def in definitions:
            play_node = self.root.add(play_def.name, data=f"play:{play_def.id}")
            hosts = list(play_def.resolved_hosts) if play_def.resolved_hosts else []

            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    role_label = Text(f"▸ Role: {entry.role}", style="cyan")
                    role_node = play_node.add(role_label, data=f"role:{entry.role}")
                    for task_def in entry.tasks:
                        self._add_task_node(role_node, task_def, hosts)
                elif isinstance(entry, TaskDefinition):
                    self._add_task_node(play_node, entry, hosts)

    def _add_task_node(self, parent, task_def, hosts: list[str]) -> None:
        """Add a task node (and its host children) under ``parent``.

        Uses the PENDING icon as the initial state — events flipping in
        later via ``apply_state_icons`` will mutate the label in place.
        """
        from ansible_aom.core.models import Status

        icon = STATUS_ICONS.get(Status.PENDING, "?")
        color = STATUS_COLORS.get(Status.PENDING, "white")
        label = Text(f"{icon} {task_def.name}", style=color)
        task_node = parent.add(label, data=f"task:{task_def.name}")

        for hostname in hosts:
            host_label = Text(f"{icon} {hostname}", style=color)
            task_node.add(host_label, data=f"host:{hostname}")

    def apply_state_icons(self, run_state) -> None:
        """Mutate existing node labels in place to reflect current status.

        Walks ``run_state.plays`` and updates icons/colors on the
        matching tree nodes by matching task and host names. Nodes added
        dynamically by JSONL events that have no preflight match fall
        through silently — the next ``populate_from_state`` (legacy
        path) or future graft logic can pick them up.
        """
        from ansible_aom.core.models import Status

        # Index existing task nodes by their data key for O(1) lookup.
        task_index: dict[str, object] = {}
        host_index: dict[tuple[str, str], object] = {}
        for play_node in self.root.children:
            for child in play_node.children:
                # child may be a role node or a task node; walk one
                # level deeper for role children.
                data = child.data or ""
                if isinstance(data, str) and data.startswith("role:"):
                    for task_node in child.children:
                        self._index_task_node(task_node, task_index, host_index)
                else:
                    self._index_task_node(child, task_index, host_index)

        for play in run_state.plays.values():
            for task in play.tasks.values():
                key = f"task:{task.name}"
                node = task_index.get(key)
                if node is not None:
                    icon = STATUS_ICONS.get(task.status, "?")
                    color = STATUS_COLORS.get(task.status, "white")
                    node.set_label(Text(f"{icon} {task.name}", style=color))
                for hostname, host_state in task.hosts.items():
                    host_node = host_index.get((task.name, hostname))
                    if host_node is not None:
                        h_icon = STATUS_ICONS.get(host_state.status, "?")
                        h_color = STATUS_COLORS.get(host_state.status, "white")
                        host_node.set_label(
                            Text(f"{h_icon} {hostname}", style=h_color)
                        )

    def _index_task_node(self, task_node, task_index: dict, host_index: dict) -> None:
        """Populate the task/host lookup tables for ``apply_state_icons``."""
        data = task_node.data or ""
        if not isinstance(data, str) or not data.startswith("task:"):
            return
        task_name = data[len("task:") :]
        task_index[data] = task_node
        for host_node in task_node.children:
            host_data = host_node.data or ""
            if isinstance(host_data, str) and host_data.startswith("host:"):
                hostname = host_data[len("host:") :]
                host_index[(task_name, hostname)] = host_node
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestTreePopulationFromDefinitions -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Confirm existing tree tests still pass**

Run: `uv run pytest tests/tui/test_tree_view.py -q`
Expected: all green (we didn't touch `populate_from_state`).

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/widgets/task_tree.py tests/tui/test_live_refresh.py
git commit -m "feat(tui): add populate_from_definitions and apply_state_icons to TaskTree

Preflight definitions now build the tree skeleton with PENDING icons;
subsequent JSONL events mutate node labels in place via
apply_state_icons rather than rebuilding the tree on every event."
```

---

## Task 3: `apply_state_icons` mutates labels in place

**Files:**
- Test: `tests/tui/test_live_refresh.py`
- (Implementation already added in Task 2 — this task verifies it works as a behavioural unit.)

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes (Task 2 already implemented this)**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestApplyStateIcons -v`
Expected: PASS (2 tests).

If a test fails here, return to Task 2 and fix the implementation — do not "fix" the test. The behavioural contract is what we shipped against.

- [ ] **Step 3: Commit**

```bash
git add tests/tui/test_live_refresh.py
git commit -m "test(tui): cover apply_state_icons in-place label mutation"
```

---

## Task 4: `MainScreen.update_from_state` calls into `TaskTree`

**Files:**
- Modify: `src/ansible_aom/tui/screens/main.py:73-111`
- Test: `tests/tui/test_live_refresh.py`

`update_from_state` already updates `SummaryPanel` and `StatusBar`. Extend it to (a) populate the tree from definitions the first time defs are present, and (b) apply state icons every call.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestMainScreenTreeIntegration -v`
Expected: FAIL — the tree has zero children because `update_from_state` never touches it.

- [ ] **Step 3: Wire `update_from_state` into the tree**

In `src/ansible_aom/tui/screens/main.py`, replace the `update_from_state` method (lines 73–111) with:

```python
    def update_from_state(self, run_state: RunState) -> None:
        """Update all widgets from RunState.

        Idempotent: safe to call on every UI tick. Tree skeleton is
        built once (when definitions first appear); subsequent calls
        only mutate icons/colors in place.
        """
        try:
            summary = self.query_one(SummaryPanel)
            status = self.query_one(StatusBar)
            tree = self.query_one(TaskTree)
        except Exception:
            # Screen not fully mounted yet; the next tick will retry.
            return

        current_play_name = ""
        hosts_total = 0
        tasks_completed = 0
        tasks_total = 0

        completed_statuses = ("ok", "changed", "failed", "skipped", "unreachable")
        host_statuses: dict[str, str] = {}

        for play in run_state.plays.values():
            if play.status.value == "running":
                current_play_name = play.name
            for task in play.tasks.values():
                tasks_total += 1
                if task.status.value in completed_statuses:
                    tasks_completed += 1
                for hostname, host_state in task.hosts.items():
                    host_statuses[hostname] = host_state.status.value

        hosts_completed = sum(1 for s in host_statuses.values() if s in completed_statuses)

        if run_state.definitions:
            for play_def in run_state.definitions:
                hosts_total = len(play_def.resolved_hosts)
                break

        summary.set_play_name(current_play_name)
        summary.set_hosts_progress(hosts_completed, hosts_total)
        summary.set_tasks_progress(tasks_completed, tasks_total)
        status.set_task_progress(tasks_completed, tasks_total)
        status.set_host_count(hosts_completed, hosts_total)
        status.set_playbook_name(run_state.playbook)

        if run_state.start_time:
            self._update_elapsed_from_start(run_state.start_time)

        # Tree handling: build the skeleton from definitions the first
        # time they're available, then apply state icons on every call.
        if run_state.definitions and not list(tree.root.children):
            tree.populate_from_definitions(run_state.definitions)
        if run_state.plays:
            tree.apply_state_icons(run_state)

        # Force a refresh — Textual reactives only fire on assignment,
        # but we mutated node labels imperatively above.
        summary.refresh()
        status.refresh()
        tree.refresh()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestMainScreenTreeIntegration -v`
Expected: PASS.

- [ ] **Step 5: Confirm panels test suite still passes**

Run: `uv run pytest tests/tui/test_panels.py -q`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/screens/main.py tests/tui/test_live_refresh.py
git commit -m "feat(tui): wire MainScreen.update_from_state into TaskTree

First definition delivery populates the tree skeleton; every
subsequent call mutates icons in place. Adds a try/except guard so
ticks that fire before the screen is fully mounted are safe no-ops."
```

---

## Task 5: Periodic refresh tick installed in `on_mount`

**Files:**
- Modify: `src/ansible_aom/tui/app.py:249-260`
- Test: `tests/tui/test_live_refresh.py`

The dirty counter and pending-log buffer accumulate; the periodic tick is what actually pushes them to the screen.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
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
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            from ansible_aom.core.models import PlayDefinition, TaskDefinition

            renderer.set_definitions(  # type: ignore[attr-defined]
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
            renderer.update_state(  # type: ignore[attr-defined]
                {
                    "_event": "v2_playbook_on_play_start",
                    "_timestamp": "2026-05-12T10:00:00Z",
                    "play": {"id": "p1", "name": "Setup"},
                }
            )
            events_done.set()
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

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
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.print_log("TASK [Install nginx] ***")  # type: ignore[attr-defined]
            renderer.print_log("ok: [web1]")  # type: ignore[attr-defined]
            printed.set()
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if printed.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)
            # The pending buffer must be drained after the tick fires.
            assert app._pending_log_lines == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestPeriodicRefresh -v`
Expected: FAIL — no tick installed; tree stays empty and pending log buffer stays full.

- [ ] **Step 3: Install the periodic tick in `on_mount` and add the refresh helper**

In `src/ansible_aom/tui/app.py`, modify the constructor's tail to track the last-seen dirty value (around line 77):

```python
        self._dirty: int = 0
        self._pending_log_lines: list[str] = []
        # Last _dirty value the periodic tick observed; used so the
        # tick can short-circuit when nothing has changed.
        self._last_seen_dirty: int = 0
```

Then add a `_refresh_widgets` method (place it just before `on_mount`, around line 248):

```python
    def _refresh_widgets(self) -> None:
        """Periodic tick: drain pending updates onto widgets.

        Runs on the Textual event loop (main thread). Reads the
        worker-set _dirty counter and only refreshes when it has
        advanced — avoids per-tick churn in idle phases.

        Guards against firing before the current screen has its
        widgets composed (screen swaps during quit confirmation, for
        instance). Any unexpected widget-state failure is logged and
        swallowed so the timer keeps running.
        """
        try:
            screen = self.screen
        except Exception:
            return
        if not screen.is_mounted:
            return

        current = self._dirty
        if current == self._last_seen_dirty and not self._pending_log_lines:
            return
        self._last_seen_dirty = current

        try:
            from ansible_aom.tui.screens.main import MainScreen

            if isinstance(screen, MainScreen):
                screen.update_from_state(self._run_state)

                # Drain any log lines queued by the worker thread.
                if self._pending_log_lines:
                    from ansible_aom.tui.widgets import LogPanel

                    try:
                        log = screen.query_one(LogPanel)
                    except Exception:
                        log = None
                    if log is not None:
                        # Snapshot-and-clear so a concurrent print_log
                        # call appending mid-iteration is picked up on
                        # the next tick rather than duplicated.
                        pending = self._pending_log_lines[:]
                        del self._pending_log_lines[: len(pending)]
                        for line in pending:
                            log.write_line(line)
        except Exception as exc:
            self.log.error(f"refresh tick error: {exc}")
```

Then update `on_mount` (lines 249–259) to install the timer:

```python
    def on_mount(self) -> None:
        """Mount the main screen and (if configured) start the playbook."""
        from ansible_aom.tui.screens.main import MainScreen

        self.push_screen(MainScreen())

        # F1: 0.2s refresh tick. nom uses ~200ms; battery-friendly,
        # imperceptible latency. The tick reads the worker-set _dirty
        # counter and only refreshes widgets when it has advanced.
        self.set_interval(0.2, self._refresh_widgets)

        # Auto-start only when constructed with a playbook target. The
        # protocol smoke tests still build a bare AOMApp() and never
        # call run() — they must not trigger a worker.
        if self._playbook is not None:
            self.run_worker(self._run_playbook_worker, thread=True, exclusive=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestPeriodicRefresh -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Run the full TUI suite**

Run: `uv run pytest tests/tui/ -q`
Expected: all green. Pay attention to `test_app_end_to_end.py` — the new tick should not break it.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/app.py tests/tui/test_live_refresh.py
git commit -m "feat(tui): install 0.2s periodic refresh tick

The tick reads the worker-set dirty counter and pushes RunState
mutations into MainScreen widgets on the main thread. Pending log
lines (queued by print_log from the worker) are drained into LogPanel
the same way. Guards screen.is_mounted to survive screen swaps."
```

---

## Task 6: Worker-thread safety via `call_from_thread`

**Files:**
- Modify: `src/ansible_aom/tui/app.py:131-160`
- Test: `tests/tui/test_live_refresh.py`

Per the approved scope adjustment, the worker uses `call_from_thread` to schedule the dirty-flag bump for `add_warning` and `print_log`. Today the bump itself is just an `int += 1` (GIL-safe), but the side effects we may add later (e.g. notification toasts) must run on the main thread. Standardise the routing now so future additions don't reintroduce a worker-touches-widget bug.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
class TestCallFromThreadRouting:
    """Worker-thread renderer callbacks marshal through the event loop."""

    @pytest.mark.asyncio
    async def test_add_warning_from_worker_lands_on_status_bar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from threading import Event

        warned = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.add_warning("[WARNING]: missing role")  # type: ignore[attr-defined]
            renderer.add_warning(  # type: ignore[attr-defined]
                "[DEPRECATION WARNING]: foo", is_deprecation=True
            )
            warned.set()
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

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
```

- [ ] **Step 2: Run test to verify it passes (already green from Task 1)**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestCallFromThreadRouting -v`
Expected: PASS.

This test serves as a regression guard for the routing pattern. Now refactor the implementation to make the threading boundary explicit so future changes don't regress.

- [ ] **Step 3: Refactor `add_warning` and `print_log` to route via `call_from_thread`**

In `src/ansible_aom/tui/app.py`, replace `add_warning` and `print_log` (around lines 131–144) with versions that explicitly schedule the dirty bump on the main thread when called from a worker:

```python
    def add_warning(self, message: str, is_deprecation: bool = False) -> None:
        """Renderer Protocol: bump counters; widgets can read them.

        Counter mutation itself is GIL-safe, but we marshal through
        ``call_from_thread`` so future side effects (toast notifications,
        StatusBar reactives, etc.) added to the dirty bump run on the
        UI thread by construction.
        """

        def _bump() -> None:
            if is_deprecation:
                self._deprecations_count += 1
            else:
                self._warnings_count += 1
            self._dirty += 1

        self._safe_call_from_thread(_bump)

    def print_log(self, message: str) -> None:
        """Renderer Protocol: append a line to the log buffer.

        Appends to ``_pending_log_lines`` which the periodic UI tick
        drains into ``LogPanel`` on the main thread.
        """

        def _enqueue() -> None:
            self._log_lines.append(message)
            self._pending_log_lines.append(message)
            self._dirty += 1

        self._safe_call_from_thread(_enqueue)

    def _safe_call_from_thread(self, fn) -> None:
        """Invoke ``fn`` on the Textual main thread when possible.

        During unit tests (no event loop) and direct synchronous calls
        from the runner-protocol smoke tests, ``call_from_thread``
        raises ``RuntimeError``; fall back to a direct call so those
        tests keep working.
        """
        try:
            self.call_from_thread(fn)
        except RuntimeError:
            fn()
```

- [ ] **Step 4: Run test to verify it still passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestCallFromThreadRouting -v`
Expected: PASS.

- [ ] **Step 5: Run the previously-passing dirty-counter tests**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestDirtyCounter -v`
Expected: PASS — `_safe_call_from_thread` falls back to direct invocation when there's no event loop, so synchronous tests still observe immediate state changes.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest tests/ -q`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add src/ansible_aom/tui/app.py tests/tui/test_live_refresh.py
git commit -m "refactor(tui): route worker-thread renderer callbacks via call_from_thread

add_warning and print_log now marshal their state mutations onto the
Textual event loop. Falls back to a direct call when no loop is
running so the protocol smoke tests still work synchronously."
```

---

## Task 7: Final refresh + title update on `handle_completion`

**Files:**
- Modify: `src/ansible_aom/tui/app.py:195-211`
- Test: `tests/tui/test_live_refresh.py`

Per the approved scope adjustment, completion does one last refresh and updates the app title with ✓ (success) or ✖ (failure/crash) so the user sees a final-state cue even if the tick was idle.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
class TestCompletionTitleUpdate:
    """handle_completion does one final refresh and updates the title."""

    @pytest.mark.asyncio
    async def test_completion_zero_marks_title_with_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from threading import Event

        done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            done.set()
            return 0

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

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
        from threading import Event

        done = Event()

        def fake_run_playbook(
            playbook: str,
            ansible_args: list[str],
            renderer: object,
            timeout: float = 0.5,
            session_dir: Path | None = None,
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.handle_completion(2, "failed")  # type: ignore[attr-defined]
            done.set()
            return 2

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

        app = AOMApp(playbook="site.yml", ansible_args=[], session_dir=tmp_path)

        async with app.run_test() as pilot:
            for _ in range(50):
                if done.is_set():
                    break
                await pilot.pause(0.02)
            await pilot.pause(0.4)

            assert "✖" in app.title
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestCompletionTitleUpdate -v`
Expected: FAIL — title currently stays at the playbook name, no marker is appended.

- [ ] **Step 3: Update `handle_completion` to set title and force a final refresh**

In `src/ansible_aom/tui/app.py`, replace `handle_completion` (lines 195–211) with:

```python
    def handle_completion(self, exit_code: int, state: str) -> None:
        """Renderer Protocol: stash final outcome; do not exit the app.

        Leaving the app running lets the user inspect the final state.
        ``stop()`` is intentionally a no-op for the same reason — the
        runner thread completes, but Textual's loop keeps spinning
        until the user presses ``q``.

        Marshals through the event loop so the title update and final
        refresh happen on the main thread (the runner worker calls
        this from a non-UI thread).
        """

        def _finish() -> None:
            self._exit_code = exit_code
            self._final_state = state
            if exit_code == 0:
                self._state = "COMPLETED"
                marker = "✓"
            elif exit_code == 1:
                self._state = "FAILED"
                marker = "✖"
            else:
                self._state = "CRASHED"
                marker = "✖"

            base = self._playbook or self.title
            # Strip a stale marker if handle_completion is called twice.
            for sym in ("✓", "✖"):
                if base.endswith(f" {sym}"):
                    base = base[: -2]
            self.title = f"{base} {marker}"

            # Force one final refresh independent of the tick cadence
            # so the user sees the terminal state immediately.
            self._dirty += 1
            self._refresh_widgets()

        self._safe_call_from_thread(_finish)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestCompletionTitleUpdate -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Confirm `test_app_end_to_end.py` still passes**

Run: `uv run pytest tests/tui/test_app_end_to_end.py -q`
Expected: all green. The existing assertions on `app.exit_code` / `app.final_state` still hold because `_finish` writes them before the title.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/tui/app.py tests/tui/test_live_refresh.py
git commit -m "feat(tui): mark app title with check/cross on completion

handle_completion now appends ✓ (exit 0) or ✖ (failure/crash) to the
window title and forces one final refresh tick so the terminal state
is visible the moment the runner returns."
```

---

## Task 8: End-to-end Pilot test — three task_starts produce three tree nodes

**Files:**
- Test: `tests/tui/test_live_refresh.py`

The headline assertion from the F1 spec: three `task_start` events feed in, the tree shows three task nodes after one tick.

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_live_refresh.py`:

```python
class TestEndToEndThreeTasks:
    """Spec headline: three task_starts → three task nodes after one tick."""

    @pytest.mark.asyncio
    async def test_three_task_starts_appear_in_tree(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from threading import Event

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
        ) -> int:
            renderer.start(playbook, ansible_args)  # type: ignore[attr-defined]
            renderer.set_definitions(  # type: ignore[attr-defined]
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
            renderer.update_state(  # type: ignore[attr-defined]
                {
                    "_event": "v2_playbook_on_play_start",
                    "_timestamp": "2026-05-12T10:00:00Z",
                    "play": {"id": "p1", "name": "Setup"},
                }
            )
            for i in range(3):
                renderer.update_state(  # type: ignore[attr-defined]
                    {
                        "_event": "v2_playbook_on_task_start",
                        "_timestamp": f"2026-05-12T10:00:0{i + 1}Z",
                        "task": {"id": f"t{i}", "name": f"Task {i}"},
                    }
                )
            events_done.set()
            renderer.handle_completion(0, "completed")  # type: ignore[attr-defined]
            return 0

        monkeypatch.setattr("ansible_aom.tui.app.run_playbook", fake_run_playbook)

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
            assert len(task_nodes) == 3, (
                f"expected 3 task nodes, got {len(task_nodes)}"
            )
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_live_refresh.py::TestEndToEndThreeTasks -v`
Expected: PASS. Everything wired in Tasks 1–7 should make this work without further implementation.

If it fails because the tree is empty: a tick didn't fire. Increase the `pilot.pause(0.4)` to `0.6` and re-run, then debug `_refresh_widgets` (likely the `screen.is_mounted` guard is over-conservative).

- [ ] **Step 3: Run the full suite one last time**

Run: `uv run pytest tests/ -q`
Expected: all green.

- [ ] **Step 4: Run lint and type-check**

Run in parallel:
```bash
uv run ruff format
uv run ruff check --fix
uv run mypy src/ansible_aom
```
Expected: no errors. The `mypy` overrides in `pyproject.toml` already relax `tui/` rules (per `CLAUDE.md`); do not add `# type: ignore` comments.

- [ ] **Step 5: Commit**

```bash
git add tests/tui/test_live_refresh.py
git commit -m "test(tui): end-to-end pilot test for three task_starts → three tree nodes

Headline acceptance test from F1 spec: feed three task_start events
through the worker-thread fake runner, wait for one refresh tick,
assert the tree shows three task nodes."
```

---

## Self-Review

**Spec coverage check (against `.sisyphus/notepads/plans/features.md` F1, lines 10–52):**

| Spec requirement | Task |
|---|---|
| `set_interval(0.2, _refresh_widgets)` in `on_mount` | Task 5 |
| `_refresh_widgets` reads `self.run_state` and calls `update_from_state` | Task 5 |
| `add_warning` / `print_log` nudge the screen via `call_from_thread` | Tasks 1, 6 |
| Log lines feed `LogPanel.write_line` via the tick | Task 5 |
| `TaskTree.populate_from_definitions(defs)` for first-time population | Task 2 |
| Subsequent state changes update node icons in place | Tasks 2, 3 |
| Don't mutate widgets from the worker thread | Tasks 1, 6 |
| Use `int` counter (GIL covers single-int writes) | Task 1 |
| Final state does one last refresh and updates title with ✓ / ✖ | Task 7 |
| Pilot test: three task_starts → three nodes after one tick | Task 8 |
| Pilot test: worker-thread `add_warning` updates StatusBar warning count | Task 6 |
| `tests/tui/test_panels.py` continues to pass | Verified after each task |
| `if not self.screen.is_mounted: return` guard inside the tick | Task 5 |

All spec items mapped.

**Placeholder scan:** searched the plan for `TBD`, `TODO`, `implement later`, `fill in details`, `add appropriate`, `handle edge cases`, "similar to". None found. Every code step ships full code.

**Type consistency check:**
- `_dirty: int`, `_pending_log_lines: list[str]`, `_last_seen_dirty: int` — declared in Task 1, read in Task 5, mutated in Tasks 1/6/7. Names match.
- `populate_from_definitions(defs)` — declared in Task 2, called from `update_from_state` in Task 4. Signature matches.
- `apply_state_icons(run_state)` — declared in Task 2, called from `update_from_state` in Task 4. Signature matches.
- `_refresh_widgets()` — declared in Task 5, called from `handle_completion` in Task 7. Signature matches (no args).
- `_safe_call_from_thread(fn)` — declared in Task 6, used in Tasks 6 and 7. Signature matches.
- Tree node `data` keys (`"play:"`, `"task:"`, `"host:"`, `"role:"`) — used consistently across `populate_from_definitions`, `_index_task_node`, and `apply_state_icons` in Task 2 and Task 3 tests.
- `MainScreen.update_from_state(run_state)` — pre-existing signature; Task 4 extends body without changing the signature.

No type drift. Plan is ready to execute.
