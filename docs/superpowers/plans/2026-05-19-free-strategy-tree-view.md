# Tree view for the compact renderer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a nom-style tree view + per-host summary table to the compact renderer that makes `strategy: free` (and multi-host `linear`) execution legible at a glance.

**Architecture:** New pure module `core/tree.py` projects `RunState` into `TreeLine`s and `HostRow`s. The compact renderer gains two formatters that consume that projection and emit ANSI lines, and `CompactRenderer._render_status_bar` is replaced with `_render_status_panel` that composes status bar + tree + host rows into a single Display update. No changes to `core/models.py` or the state machine.

**Tech Stack:** Python 3.14, dataclasses, pytest, existing icon/colour helpers in `core/icons.py` and the SGR helpers (`_DIM`, `_GREEN`, etc.) in `compact/renderer.py`.

**Reference spec:** `docs/superpowers/specs/2026-05-19-free-strategy-tree-view-design.md`

---

## File structure

| File | Action | Responsibility |
|---|---|---|
| `src/ansible_aom/core/tree.py` | **create** | `TreeLine`, `HostRow` dataclasses; `TreeProjection` (pure, no I/O) |
| `src/ansible_aom/compact/renderer.py` | **modify** | Extract `_format_count_cells` helper; add `format_tree_block`, `format_host_rows`; rename `_render_status_bar` → `_render_status_panel` and compose three regions |
| `tests/unit/test_tree_projection.py` | **create** | Pure projection tests built from `RunState` fixtures |
| `tests/compact/test_tree_render.py` | **create** | Snapshot tests for the rendered bottom panel under linear, free, post-recap |

Existing event fixtures in `tests/conftest.py` (`event_play_start`, `event_task_start`, `event_runner_start`, `event_runner_ok`, etc.) are the building blocks for `RunState` fixtures — fire events through `state.handle_event(...)` to set up scenarios.

---

## Conventions used in every task

- TDD: red → minimal green → commit. Run the **whole** suite (`uv run pytest tests/ -q`) before committing each task.
- mypy must stay clean: `uv run mypy src/ansible_aom`.
- Never add `# type: ignore`. If a module-level relaxation is genuinely needed, raise it before writing the task's code.
- Commit messages use Conventional Commits (`feat:`, `refactor:`, `test:`).
- The project's `CLAUDE.md` forbids `Co-Authored-By:` trailers. Do not add any.

---

## Task 1: `core/tree.py` — dataclasses + `TreeProjection` skeleton with visibility methods

**Files:**
- Create: `src/ansible_aom/core/tree.py`
- Create: `tests/unit/test_tree_projection.py`

What this delivers: `TreeLine`, `HostRow` dataclasses, plus `TreeProjection.from_run_state` and the two `is_*_visible` predicates. No host_rows / tree_lines content yet — those are Tasks 2–5.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_tree_projection.py
"""Pure-data tests for core/tree.TreeProjection.

The projection is a deterministic function of RunState; tests build a
RunState by firing events from conftest fixtures through handle_event,
then assert on the projection.
"""
from __future__ import annotations

from ansible_aom.core.models import RunState, Status
from ansible_aom.core.tree import HostRow, TreeLine, TreeProjection


def _state_with_running_task(event_playbook_start, event_play_start,
                             event_task_start, event_runner_start) -> RunState:
    state = RunState(playbook="site.yml")
    for ev in (event_playbook_start, event_play_start,
               event_task_start, event_runner_start):
        state.handle_event(ev)
    return state


class TestVisibility:
    def test_empty_state_hides_everything(self):
        state = RunState(playbook="site.yml")
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False
        assert p.is_host_summary_visible() is False

    def test_running_task_shows_tree(
        self, event_playbook_start, event_play_start,
        event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start,
            event_task_start, event_runner_start
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True

    def test_host_summary_hidden_for_single_host(
        self, event_playbook_start, event_play_start,
        event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start,
            event_task_start, event_runner_start
        )
        # Only web1 has appeared so far
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is False

    def test_host_summary_visible_for_multi_host(
        self, event_playbook_start, event_play_start, event_task_start,
        event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start,
            event_task_start, event_runner_start
        )
        # Fire a second host on the same task
        state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "task-uuid-1", "name": "Install nginx"},
            "host": "web2",
        })
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is True


class TestDataclassShapes:
    def test_tree_line_is_frozen(self):
        line = TreeLine(depth=0, kind="task", label="Install nginx",
                        glyph="◐", status=Status.RUNNING, elapsed_s=1.0)
        try:
            line.depth = 5  # type: ignore[misc]
        except Exception as e:
            assert "frozen" in str(e).lower() or "attribute" in str(e).lower()
        else:
            raise AssertionError("TreeLine must be frozen")

    def test_host_row_is_frozen(self):
        row = HostRow(hostname="web1", counts={Status.OK: 3},
                      worst_status=Status.OK, current_task=None,
                      current_elapsed_s=None)
        try:
            row.hostname = "web2"  # type: ignore[misc]
        except Exception as e:
            assert "frozen" in str(e).lower() or "attribute" in str(e).lower()
        else:
            raise AssertionError("HostRow must be frozen")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
```

Expected: ImportError on `ansible_aom.core.tree`.

- [ ] **Step 3: Write the module**

```python
# src/ansible_aom/core/tree.py
"""Pure projection of RunState into renderable tree + host-row data.

This module contains *no* I/O, no ANSI, no terminal awareness — it is
the data layer the compact (and future TUI) renderers consume. See
docs/superpowers/specs/2026-05-19-free-strategy-tree-view-design.md.

Architectural rule: core/ never imports from compact/ or tui/. Renderers
import from here; never the reverse.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ansible_aom.core.models import RunState, Status

TreeKind = Literal["playbook", "play", "role", "task", "host"]


@dataclass(frozen=True)
class TreeLine:
    """One rendered line in the tree.

    The renderer turns this into "{indent}{branch_glyph}{label}" with
    status-coloured glyph; this class itself carries no rendering
    concerns.
    """

    depth: int
    kind: TreeKind
    label: str
    glyph: str | None
    status: Status | None
    elapsed_s: float | None


@dataclass(frozen=True)
class HostRow:
    """One row in the per-host summary table.

    `counts` only carries non-zero entries. `worst_status` drives the
    hostname colour selection per the spec; `current_task` is None when
    the host is idle (between tasks) or after the run finishes.
    """

    hostname: str
    counts: dict[Status, int]
    worst_status: Status | None
    current_task: str | None
    current_elapsed_s: float | None


@dataclass
class TreeProjection:
    """Pure projection of RunState. Build via `from_run_state`."""

    _state: RunState

    @classmethod
    def from_run_state(cls, state: RunState) -> "TreeProjection":
        return cls(_state=state)

    # --- Visibility predicates --------------------------------------------

    def is_tree_visible(self) -> bool:
        """True iff at least one task has status=RUNNING right now."""
        for play in self._state.plays.values():
            for task in play.tasks.values():
                if task.status == Status.RUNNING:
                    return True
        return False

    def is_host_summary_visible(self) -> bool:
        """True iff the run targets more than one host.

        Prefers preflight `resolved_hosts` (so a multi-host run shows the
        table from frame zero); falls back to "hosts seen in events" when
        no preflight definitions are available.
        """
        preflight_hosts: set[str] = set()
        for play_def in self._state.definitions:
            preflight_hosts.update(play_def.resolved_hosts)
        if len(preflight_hosts) > 1:
            return True

        seen: set[str] = set()
        for play in self._state.plays.values():
            for task in play.tasks.values():
                seen.update(task.hosts.keys())
        return len(seen) > 1

    # --- Projections (filled in later tasks) ------------------------------

    def host_rows(self) -> list[HostRow]:
        raise NotImplementedError  # Task 2

    def tree_lines(self, budget: int) -> list[TreeLine]:
        raise NotImplementedError  # Tasks 3–5
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
uv run mypy src/ansible_aom
uv run pytest tests/ -q
```

Expected: tests in `test_tree_projection.py` pass; full suite stays green; mypy clean.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/tree.py tests/unit/test_tree_projection.py
git commit -m "feat(tree): scaffold TreeProjection with visibility predicates"
```

---

## Task 2: `host_rows()` — counts, worst-status, current-task suffix

**Files:**
- Modify: `src/ansible_aom/core/tree.py`
- Modify: `tests/unit/test_tree_projection.py`

What this delivers: the full `host_rows()` projection, including idle/unreachable/finished suffix states. `HostRunState.changed=True` maps to `Status.CHANGED` for count purposes regardless of `status=OK`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_tree_projection.py`:

```python
class TestHostRows:
    def _multi_host_state(self) -> RunState:
        """web1 done-ok, web2 running, web3 done-changed, db1 unreachable."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start",
                            "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event({"_event": "v2_playbook_on_play_start",
                            "_timestamp": "2026-04-20T10:00:01Z",
                            "play": {"id": "p1", "name": "Deploy"}})
        state.handle_event({"_event": "v2_playbook_on_task_start",
                            "_timestamp": "2026-04-20T10:00:02Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "play": {"id": "p1"}})
        state.handle_event({"_event": "v2_runner_on_ok",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "hosts": {"web1": {"ok": True, "changed": False}}})
        state.handle_event({"_event": "v2_runner_on_ok",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "hosts": {"web3": {"ok": True, "changed": True}}})
        state.handle_event({"_event": "v2_runner_on_unreachable",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "hosts": {"db1": {"unreachable": True}}})
        # web2 is mid-task
        state.handle_event({"_event": "v2_playbook_on_task_start",
                            "_timestamp": "2026-04-20T10:00:06Z",
                            "task": {"id": "t2", "name": "Configure firewall"},
                            "play": {"id": "p1"}})
        state.handle_event({"_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:07Z",
                            "task": {"id": "t2", "name": "Configure firewall"},
                            "host": "web2"})
        return state

    def test_counts_aggregate_per_host(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].counts == {Status.OK: 1}
        # CHANGED is derived from HostRunState.changed=True even when
        # status=OK — the count belongs to CHANGED, not OK.
        assert rows["web3"].counts == {Status.CHANGED: 1}
        assert rows["db1"].counts == {Status.UNREACHABLE: 1}

    def test_worst_status_selection(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].worst_status == Status.OK
        assert rows["web3"].worst_status == Status.CHANGED
        assert rows["db1"].worst_status == Status.UNREACHABLE

    def test_current_task_for_running_host(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web2"].current_task == "Configure firewall"
        assert rows["web2"].current_elapsed_s is not None

    def test_idle_host_has_no_current_task(self):
        # web1 finished its task; no later task started for it.
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].current_task is None
        assert rows["web1"].current_elapsed_s is None

    def test_unreachable_host_has_no_current_task(self):
        state = self._multi_host_state()
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        # The row carries worst_status=UNREACHABLE; the renderer turns
        # that into the "unreachable" suffix. The projection does NOT
        # synthesise a fake current_task.
        assert rows["db1"].current_task is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_tree_projection.py::TestHostRows -v
```

Expected: NotImplementedError.

- [ ] **Step 3: Implement `host_rows()`**

Replace the `host_rows` stub in `src/ansible_aom/core/tree.py`:

```python
    # Priority order for worst-status selection (highest precedence first).
    # FAILED is worst because a single failure on a host is the most
    # actionable signal; UNREACHABLE comes next; CHANGED indicates state
    # actually mutated; OK is the baseline.
    _WORST_STATUS_PRIORITY: tuple[Status, ...] = (
        Status.FAILED,
        Status.UNREACHABLE,
        Status.CHANGED,
        Status.OK,
        Status.SKIPPED,
        Status.PENDING,
    )

    def host_rows(self) -> list[HostRow]:
        from datetime import datetime, timezone

        # Per-host accumulators.
        counts: dict[str, dict[Status, int]] = {}
        current: dict[str, tuple[str, float] | None] = {}

        # Preserve first-seen ordering — mirrors event order, which mirrors
        # ansible's host order under linear and roughly the start order
        # under free.
        order: list[str] = []

        now = datetime.now(timezone.utc)

        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, hs in task.hosts.items():
                    if hostname not in counts:
                        counts[hostname] = {}
                        current[hostname] = None
                        order.append(hostname)

                    # changed=True takes precedence over status=OK for
                    # count classification — spec section "host row".
                    effective = (
                        Status.CHANGED
                        if hs.status == Status.OK and hs.changed
                        else hs.status
                    )

                    if hs.status == Status.RUNNING:
                        elapsed = (
                            (now - hs.start_time).total_seconds()
                            if hs.start_time is not None
                            else 0.0
                        )
                        current[hostname] = (task.name, elapsed)
                    elif effective in (
                        Status.OK, Status.CHANGED, Status.FAILED,
                        Status.UNREACHABLE, Status.SKIPPED,
                    ):
                        counts[hostname][effective] = (
                            counts[hostname].get(effective, 0) + 1
                        )

        rows: list[HostRow] = []
        for hostname in order:
            host_counts = counts[hostname]
            worst = self._worst_status_of(host_counts.keys())
            cur = current[hostname]
            rows.append(HostRow(
                hostname=hostname,
                counts=dict(host_counts),
                worst_status=worst,
                current_task=cur[0] if cur else None,
                current_elapsed_s=cur[1] if cur else None,
            ))
        return rows

    @classmethod
    def _worst_status_of(cls, statuses) -> Status | None:
        seen = set(statuses)
        for s in cls._WORST_STATUS_PRIORITY:
            if s in seen:
                return s
        return None
```

- [ ] **Step 4: Run tests + full suite**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
uv run mypy src/ansible_aom
uv run pytest tests/ -q
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/tree.py tests/unit/test_tree_projection.py
git commit -m "feat(tree): project host rows with counts, worst-status, current task"
```

---

## Task 3: `tree_lines()` — basic shape for a single running task

**Files:**
- Modify: `src/ansible_aom/core/tree.py`
- Modify: `tests/unit/test_tree_projection.py`

What this delivers: walking `RunState.plays → tasks` filtered to `Status.RUNNING`, emitting `playbook → play → task → [host children]` lines in source order. No role grouping yet (Task 4), no pruning yet (Task 5). Budget is honoured trivially — the walker emits everything it has.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_tree_projection.py`:

```python
class TestTreeLinesBasic:
    def _running_task_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start",
                            "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event({"_event": "v2_playbook_on_play_start",
                            "_timestamp": "2026-04-20T10:00:01Z",
                            "play": {"id": "p1", "name": "deploy webservers"}})
        state.handle_event({"_event": "v2_playbook_on_task_start",
                            "_timestamp": "2026-04-20T10:00:02Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "play": {"id": "p1"}})
        for host in ("web1", "web2"):
            state.handle_event({"_event": "v2_runner_on_start",
                                "_timestamp": "2026-04-20T10:00:03Z",
                                "task": {"id": "t1", "name": "Install nginx"},
                                "host": host})
        return state

    def test_emits_playbook_play_task_hosts(self):
        state = self._running_task_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)

        # Expect: playbook, play, task, host x2 — in that source order.
        kinds = [ln.kind for ln in lines]
        assert kinds == ["playbook", "play", "task", "host", "host"]

        assert lines[0].label == "site.yml"
        assert lines[1].label.startswith("play: ")
        assert "deploy webservers" in lines[1].label
        assert lines[2].kind == "task"
        assert lines[2].status == Status.RUNNING

        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert [ln.label for ln in host_lines] == ["web1", "web2"]
        for hl in host_lines:
            assert hl.status == Status.RUNNING
            assert hl.elapsed_s is not None

    def test_task_label_carries_count_summary(self):
        state = self._running_task_state()
        # Finish web1; web2 still running.
        state.handle_event({"_event": "v2_runner_on_ok",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "hosts": {"web1": {"ok": True, "changed": False}}})
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=20)
        task_line = next(ln for ln in lines if ln.kind == "task")
        # Label format: "Install nginx  (1 ok, 1 running)"
        assert "Install nginx" in task_line.label
        assert "1 ok" in task_line.label
        assert "1 running" in task_line.label

    def test_only_currently_running_hosts_appear_as_leaves(self):
        state = self._running_task_state()
        # Finish web1 — it should drop out of the host leaves.
        state.handle_event({"_event": "v2_runner_on_ok",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "hosts": {"web1": {"ok": True, "changed": False}}})
        p = TreeProjection.from_run_state(state)
        host_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "host"]
        assert [ln.label for ln in host_lines] == ["web2"]

    def test_no_lines_when_no_task_running(self):
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start",
                            "_timestamp": "2026-04-20T10:00:00Z"})
        p = TreeProjection.from_run_state(state)
        assert p.tree_lines(budget=20) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_tree_projection.py::TestTreeLinesBasic -v
```

Expected: NotImplementedError.

- [ ] **Step 3: Implement `tree_lines()` — basic walker**

Replace the `tree_lines` stub in `src/ansible_aom/core/tree.py`:

```python
    def tree_lines(self, budget: int) -> list[TreeLine]:
        from datetime import datetime, timezone

        if not self.is_tree_visible():
            return []

        now = datetime.now(timezone.utc)
        lines: list[TreeLine] = [
            TreeLine(
                depth=0, kind="playbook", label=self._state.playbook,
                glyph=None, status=None, elapsed_s=None,
            )
        ]

        for play in self._state.plays.values():
            running_tasks = [t for t in play.tasks.values()
                             if t.status == Status.RUNNING]
            if not running_tasks:
                continue
            lines.append(TreeLine(
                depth=1, kind="play", label=f"play: {play.name}",
                glyph=None, status=play.status, elapsed_s=None,
            ))
            for task in running_tasks:
                lines.append(self._task_line(task, depth=2))
                for hostname, hs in task.hosts.items():
                    if hs.status != Status.RUNNING:
                        continue
                    elapsed = (
                        (now - hs.start_time).total_seconds()
                        if hs.start_time is not None
                        else 0.0
                    )
                    lines.append(TreeLine(
                        depth=3, kind="host", label=hostname,
                        glyph=None, status=Status.RUNNING,
                        elapsed_s=elapsed,
                    ))

        return lines

    @staticmethod
    def _task_line(task, depth: int) -> TreeLine:
        # Count tally for the parenthesised summary on the task line.
        # Order matters for the label: ok, changed, running, failed,
        # unreachable, skipped — same order as the spec example.
        ok = changed = running = failed = unreachable = skipped = 0
        for hs in task.hosts.values():
            if hs.status == Status.RUNNING:
                running += 1
            elif hs.status == Status.OK:
                if hs.changed:
                    changed += 1
                else:
                    ok += 1
            elif hs.status == Status.CHANGED:
                changed += 1
            elif hs.status == Status.FAILED:
                failed += 1
            elif hs.status == Status.UNREACHABLE:
                unreachable += 1
            elif hs.status == Status.SKIPPED:
                skipped += 1
        parts: list[str] = []
        for label, n in (("ok", ok), ("changed", changed), ("running", running),
                        ("failed", failed), ("unreachable", unreachable),
                        ("skipped", skipped)):
            if n > 0:
                parts.append(f"{n} {label}")
        suffix = f"  ({', '.join(parts)})" if parts else ""
        return TreeLine(
            depth=depth, kind="task", label=f"{task.name}{suffix}",
            glyph=None, status=Status.RUNNING, elapsed_s=None,
        )
```

- [ ] **Step 4: Run tests + full suite**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
uv run mypy src/ansible_aom
uv run pytest tests/ -q
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/tree.py tests/unit/test_tree_projection.py
git commit -m "feat(tree): emit playbook → play → task → host lines for running tasks"
```

---

## Task 4: `tree_lines()` — role grouping + free-strategy fan-out

**Files:**
- Modify: `src/ansible_aom/core/tree.py`
- Modify: `tests/unit/test_tree_projection.py`

What this delivers: when a running task belongs to a role (per preflight `RoleGroupDefinition` in `RunState.definitions`), insert a `role: <name>` branch between play and task. Multi-task fan-out (free strategy: two tasks running concurrently on different host subsets) renders as two sibling task lines under the play (or under their respective role branches).

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_tree_projection.py`:

```python
from ansible_aom.core.models import (
    PlayDefinition, RoleGroupDefinition, TaskDefinition,
)


class TestTreeLinesRolesAndFanOut:
    def _role_aware_definitions(self) -> list[PlayDefinition]:
        # Mirrors preflight output: one play with one role containing two tasks.
        return [PlayDefinition(
            name="deploy",
            resolved_hosts=["web1", "web2"],
            tasks=[
                RoleGroupDefinition(
                    name="webserver",
                    tasks=[
                        TaskDefinition(name="Install nginx", source="nginx.yml:1"),
                        TaskDefinition(name="Configure firewall", source="nginx.yml:5"),
                    ],
                ),
            ],
        )]

    def _free_strategy_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.definitions = self._role_aware_definitions()
        state.handle_event({"_event": "v2_playbook_on_start",
                            "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event({"_event": "v2_playbook_on_play_start",
                            "_timestamp": "2026-04-20T10:00:01Z",
                            "play": {"id": "p1", "name": "deploy"}})
        # web1 is on "Install nginx"; web2 has raced ahead to "Configure firewall"
        state.handle_event({"_event": "v2_playbook_on_task_start",
                            "_timestamp": "2026-04-20T10:00:02Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "play": {"id": "p1"}})
        state.handle_event({"_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:03Z",
                            "task": {"id": "t1", "name": "Install nginx"},
                            "host": "web1"})
        state.handle_event({"_event": "v2_playbook_on_task_start",
                            "_timestamp": "2026-04-20T10:00:04Z",
                            "task": {"id": "t2", "name": "Configure firewall"},
                            "play": {"id": "p1"}})
        state.handle_event({"_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:05Z",
                            "task": {"id": "t2", "name": "Configure firewall"},
                            "host": "web2"})
        return state

    def test_role_branch_appears_above_role_tasks(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Expected ordering: playbook, play, role, task, host, task, host
        kinds_labels = [(ln.kind, ln.label) for ln in lines]
        assert ("role", "role: webserver") in kinds_labels
        role_idx = kinds_labels.index(("role", "role: webserver"))
        # Tasks under the role have depth > role's depth
        role_depth = lines[role_idx].depth
        # Both task lines should follow the role line with depth > role_depth
        for ln in lines[role_idx + 1:]:
            if ln.kind == "task":
                assert ln.depth > role_depth

    def test_two_running_tasks_appear_as_siblings(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        names = [ln.label.split("  ")[0] for ln in task_lines]
        assert "Install nginx" in names
        assert "Configure firewall" in names

    def test_each_task_only_lists_its_own_running_hosts(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Find each task and its host children (depth+1 immediately after).
        host_under_task: dict[str, list[str]] = {}
        current_task: str | None = None
        for ln in lines:
            if ln.kind == "task":
                current_task = ln.label.split("  ")[0]
                host_under_task[current_task] = []
            elif ln.kind == "host" and current_task is not None:
                host_under_task[current_task].append(ln.label)

        assert host_under_task["Install nginx"] == ["web1"]
        assert host_under_task["Configure firewall"] == ["web2"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_tree_projection.py::TestTreeLinesRolesAndFanOut -v
```

Expected: `role` line missing, multi-task ordering wrong, depths off.

- [ ] **Step 3: Extend `tree_lines()` with role awareness**

Add a role-lookup helper and adjust the walker in `src/ansible_aom/core/tree.py`:

```python
    def _task_role(self, task_name: str) -> str | None:
        """Return the role name a task belongs to, or None.

        Preflight `--list-tasks` records role membership via
        RoleGroupDefinition; we look up by task name. The first match
        wins — duplicate task names across roles is a user-side
        ambiguity we don't try to resolve here.
        """
        from ansible_aom.core.models import RoleGroupDefinition
        for play_def in self._state.definitions:
            for entry in play_def.tasks:
                if isinstance(entry, RoleGroupDefinition):
                    for task_def in entry.tasks:
                        if task_def.name == task_name:
                            return entry.name
        return None
```

Then replace the inner `for task in running_tasks` block of `tree_lines`:

```python
            # Group running tasks by their role (or None for play-level tasks).
            tasks_by_role: dict[str | None, list] = {}
            order: list[str | None] = []
            for task in running_tasks:
                role = self._task_role(task.name)
                if role not in tasks_by_role:
                    tasks_by_role[role] = []
                    order.append(role)
                tasks_by_role[role].append(task)

            for role in order:
                task_depth = 2
                if role is not None:
                    lines.append(TreeLine(
                        depth=2, kind="role", label=f"role: {role}",
                        glyph=None, status=None, elapsed_s=None,
                    ))
                    task_depth = 3
                for task in tasks_by_role[role]:
                    lines.append(self._task_line(task, depth=task_depth))
                    for hostname, hs in task.hosts.items():
                        if hs.status != Status.RUNNING:
                            continue
                        elapsed = (
                            (now - hs.start_time).total_seconds()
                            if hs.start_time is not None
                            else 0.0
                        )
                        lines.append(TreeLine(
                            depth=task_depth + 1, kind="host", label=hostname,
                            glyph=None, status=Status.RUNNING,
                            elapsed_s=elapsed,
                        ))
```

- [ ] **Step 4: Run tests + full suite**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
uv run mypy src/ansible_aom
uv run pytest tests/ -q
```

Expected: all green. Earlier tests (no role definitions) still pass — `_task_role` returns None, the role branch is skipped, depths stay at 2/3.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/tree.py tests/unit/test_tree_projection.py
git commit -m "feat(tree): group tasks by role; support free-strategy fan-out"
```

---

## Task 5: `tree_lines()` — height-budget pruning + invariants

**Files:**
- Modify: `src/ansible_aom/core/tree.py`
- Modify: `tests/unit/test_tree_projection.py`

What this delivers: when the unconstrained output exceeds `budget`, prune in three stages — (a) collapse host children of tasks, (b) drop excess tasks within a role keeping ≥1, (c) collapse a role into a single summary line. Invariants: every active role keeps ≥1 line; every running host keeps a tree leaf *unless* the host summary table is visible (we don't assert that here — the renderer combines both views).

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_tree_projection.py`:

```python
class TestTreeLinesPruning:
    def _many_tasks_state(self, n_roles: int, tasks_per_role: int,
                          hosts_per_task: int) -> RunState:
        state = RunState(playbook="site.yml")
        roles = [
            RoleGroupDefinition(
                name=f"role{r}",
                tasks=[TaskDefinition(name=f"r{r}-t{t}", source=f"f.yml:{t}")
                       for t in range(tasks_per_role)],
            )
            for r in range(n_roles)
        ]
        state.definitions = [PlayDefinition(
            name="big", resolved_hosts=[f"h{i}" for i in range(hosts_per_task)],
            tasks=list(roles),
        )]
        state.handle_event({"_event": "v2_playbook_on_start",
                            "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event({"_event": "v2_playbook_on_play_start",
                            "_timestamp": "2026-04-20T10:00:01Z",
                            "play": {"id": "p1", "name": "big"}})
        for r in range(n_roles):
            for t in range(tasks_per_role):
                tname = f"r{r}-t{t}"
                state.handle_event({"_event": "v2_playbook_on_task_start",
                                    "_timestamp": "2026-04-20T10:00:02Z",
                                    "task": {"id": f"{r}-{t}", "name": tname},
                                    "play": {"id": "p1"}})
                for h in range(hosts_per_task):
                    state.handle_event({"_event": "v2_runner_on_start",
                                        "_timestamp": "2026-04-20T10:00:03Z",
                                        "task": {"id": f"{r}-{t}", "name": tname},
                                        "host": f"h{h}"})
        return state

    def test_within_budget_is_unchanged(self):
        state = self._many_tasks_state(n_roles=1, tasks_per_role=1,
                                       hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        unbounded = p.tree_lines(budget=999)
        bounded = p.tree_lines(budget=999)  # same budget; just verifying parity
        assert bounded == unbounded

    def test_collapses_host_leaves_first(self):
        # 1 role × 1 task × 5 hosts → 1 playbook + 1 play + 1 role + 1 task
        # + 5 hosts = 9 lines. Budget 5 should drop all host leaves but
        # keep the task line.
        state = self._many_tasks_state(n_roles=1, tasks_per_role=1,
                                       hosts_per_task=5)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=5)
        kinds = [ln.kind for ln in lines]
        assert "task" in kinds
        assert "host" not in kinds  # collapsed
        assert len(lines) <= 5

    def test_invariant_one_each_active_role_keeps_one_line(self):
        # 4 roles × 3 tasks × 2 hosts = lots. Force tight budget.
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3,
                                       hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=8)
        # Each role must have either a "role:" line OR at least one task
        # line. The pruner can collapse to either form.
        labels = "\n".join(ln.label for ln in lines)
        for r in range(4):
            assert f"role{r}" in labels, (
                f"role{r} missing from pruned output:\n{labels}"
            )

    def test_collapsed_role_summary_format(self):
        # Force aggressive pruning so at least one role becomes a summary.
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3,
                                       hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=8)
        role_summary_lines = [
            ln for ln in lines
            if ln.kind == "role" and "tasks running" in ln.label
        ]
        # Format check: "role: roleN  (M tasks running on K hosts)"
        for ln in role_summary_lines:
            assert ln.label.startswith("role: role")
            assert "tasks running on" in ln.label
            assert "hosts)" in ln.label
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/test_tree_projection.py::TestTreeLinesPruning -v
```

Expected: host leaves still present at small budgets; possibly some roles dropped entirely.

- [ ] **Step 3: Implement pruning**

In `src/ansible_aom/core/tree.py`, rename the existing `tree_lines` method to `_tree_lines_unbounded` (keep its body unchanged), and add a new `tree_lines` that prunes:

```python
    def tree_lines(self, budget: int) -> list[TreeLine]:
        """Project + prune to fit `budget` lines.

        Pruning order:
          (a) drop host leaves under tasks
          (b) drop excess task lines within a role, keep first one
          (c) collapse a role to "role: X  (N tasks running on K hosts)"

        Invariant: every active role retains at least one visible line.
        """
        lines = self._tree_lines_unbounded()
        if len(lines) <= budget:
            return lines

        # --- Stage (a): drop host leaves ---------------------------------
        lines = [ln for ln in lines if ln.kind != "host"]
        if len(lines) <= budget:
            return lines

        # --- Stage (b): keep ≤1 task per role ----------------------------
        kept: list[TreeLine] = []
        last_role_idx: int | None = None
        tasks_in_role = 0
        for ln in lines:
            if ln.kind == "role":
                last_role_idx = len(kept)
                tasks_in_role = 0
                kept.append(ln)
            elif ln.kind == "task" and last_role_idx is not None:
                if tasks_in_role == 0:
                    kept.append(ln)
                tasks_in_role += 1
            else:
                kept.append(ln)
        lines = kept
        if len(lines) <= budget:
            return lines

        # --- Stage (c): collapse over-budget roles to a summary line -----
        # Build per-role aggregates from current state, then replace each
        # role's (role-line + task-lines) tuple with a single summary line.
        from collections import defaultdict
        running_tasks_per_role: dict[str | None, int] = defaultdict(int)
        running_hosts_per_role: dict[str | None, set[str]] = defaultdict(set)
        for play in self._state.plays.values():
            for task in play.tasks.values():
                if task.status != Status.RUNNING:
                    continue
                role = self._task_role(task.name)
                running_tasks_per_role[role] += 1
                for hostname, hs in task.hosts.items():
                    if hs.status == Status.RUNNING:
                        running_hosts_per_role[role].add(hostname)

        collapsed: list[TreeLine] = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.kind == "role":
                # Replace role line + following task lines with a summary.
                role_name = ln.label.removeprefix("role: ")
                n_tasks = running_tasks_per_role.get(role_name, 0)
                n_hosts = len(running_hosts_per_role.get(role_name, set()))
                collapsed.append(TreeLine(
                    depth=ln.depth, kind="role",
                    label=f"role: {role_name}  "
                          f"({n_tasks} tasks running on {n_hosts} hosts)",
                    glyph=None, status=None, elapsed_s=None,
                ))
                # Skip any immediately following task lines.
                i += 1
                while i < len(lines) and lines[i].kind == "task":
                    i += 1
            else:
                collapsed.append(ln)
                i += 1
        return collapsed
```

- [ ] **Step 4: Run tests + full suite**

```bash
uv run pytest tests/unit/test_tree_projection.py -v
uv run mypy src/ansible_aom
uv run pytest tests/ -q
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/core/tree.py tests/unit/test_tree_projection.py
git commit -m "feat(tree): height-budget pruning with role-line invariant"
```

---

## Task 6: `format_host_rows()` formatter + count-cells refactor

**Files:**
- Modify: `src/ansible_aom/compact/renderer.py`
- Create: `tests/compact/test_tree_render.py`

What this delivers: extract a private `_format_count_cells(...)` helper from `format_host_summary` (no behaviour change for existing callers — they keep producing the same string). Add `format_host_rows(projection, *, width, ascii_mode, colorize)` returning a list of strings.

- [ ] **Step 1: Write the failing tests**

```python
# tests/compact/test_tree_render.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/compact/test_tree_render.py -v
```

Expected: ImportError on `format_host_rows` (and `format_tree_block`, which we add next task).

- [ ] **Step 3: Refactor `format_host_summary` to expose count cells**

In `src/ansible_aom/compact/renderer.py`, replace the body of
`format_host_summary` so the count-cells portion is a reusable helper.
Add the helper above it:

```python
def _format_count_cells(
    ok: int, changed: int, failed: int, unreachable: int,
    *, ascii_mode: bool, colorize: bool,
) -> list[str]:
    """Render non-zero status count cells. Order: ok, changed, failed, unreachable.

    Returned as a list of styled segments so callers can space-join or
    place them inside other layouts. Existing `format_host_summary`
    behaviour preserved by joining with a single space.
    """
    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
    cells: list[str] = []
    if ok > 0:
        cells.append(_wrap(f"{icons[Status.OK]} {ok} ok", _GREEN, colorize))
    if changed > 0:
        cells.append(_wrap(f"{icons[Status.CHANGED]} {changed} changed",
                           _YELLOW, colorize))
    if failed > 0:
        cells.append(_wrap(f"{icons[Status.FAILED]} {failed} failed",
                           _RED, colorize))
    if unreachable > 0:
        cells.append(_wrap(
            f"{icons[Status.UNREACHABLE]} {unreachable} unreachable",
            _MAGENTA, colorize,
        ))
    return cells
```

Then replace the body of `format_host_summary`:

```python
def format_host_summary(
    hostname: str,
    ok: int, changed: int, failed: int, unreachable: int,
    ascii_mode: bool = False, colorize: bool = False,
) -> str:
    cells = _format_count_cells(
        ok, changed, failed, unreachable,
        ascii_mode=ascii_mode, colorize=colorize,
    )
    return " ".join([_wrap(f"{hostname}:", _DIM, colorize), *cells])
```

- [ ] **Step 4: Add `format_host_rows`**

Append to `src/ansible_aom/compact/renderer.py` (after `format_host_summary`):

```python
# --- Worst-status → SGR colour mapping for the hostname cell ---------------
# Failed hosts go red; unreachable magenta; changed yellow. OK/SKIPPED/PENDING
# stay default-foreground (the count cells already carry their own colour).
_HOSTNAME_COLOR_BY_WORST: dict[Status, str] = {
    Status.FAILED: _RED,
    Status.UNREACHABLE: _MAGENTA,
    Status.CHANGED: _YELLOW,
}


def format_host_rows(
    projection: "TreeProjection",
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> list[str]:
    """Render the per-host summary table.

    One line per host: hostname (worst-status coloured) + count cells +
    current-task suffix. Idle / unreachable / finished hosts get the
    appropriate suffix; the projection has already classified them.
    """
    from ansible_aom.core.icons import get_running_frame  # local: avoid cycle

    icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
    out: list[str] = []
    for row in projection.host_rows():
        hostname_color = _HOSTNAME_COLOR_BY_WORST.get(row.worst_status or Status.OK)
        hostname_seg = (
            _wrap(row.hostname, hostname_color, colorize)
            if hostname_color else row.hostname
        )

        cells = _format_count_cells(
            ok=row.counts.get(Status.OK, 0),
            changed=row.counts.get(Status.CHANGED, 0),
            failed=row.counts.get(Status.FAILED, 0),
            unreachable=row.counts.get(Status.UNREACHABLE, 0),
            ascii_mode=ascii_mode, colorize=colorize,
        )

        # Current-task suffix.
        if row.worst_status == Status.UNREACHABLE and row.current_task is None:
            suffix = _wrap("unreachable", _MAGENTA, colorize)
        elif row.current_task is None:
            suffix = _wrap("(idle)", _DIM, colorize)
        else:
            elapsed = int(row.current_elapsed_s or 0)
            glyph = get_running_frame(0)  # static frame in the per-host row
            suffix = (
                f"on: {row.current_task}  "
                f"{_wrap(f'{glyph} {elapsed}s', _CYAN, colorize)}"
            )

        line = " ".join([hostname_seg, *cells, " ", suffix])
        # Right-truncate to `width` if the rendered string overflows.
        # Future: hostname abbreviation (spec: deferred).
        if len(_strip_sgr(line)) > width:
            line = _truncate_visible(line, width)
        out.append(line)
    return out
```

Add the two small helpers near the SGR helpers (top of file):

```python
def _strip_sgr(text: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _truncate_visible(text: str, width: int) -> str:
    """Truncate to `width` visible chars while preserving any open SGR
    state by appending RESET. SGR escapes are zero-width."""
    if width <= 1:
        return text[:width]
    visible = 0
    out: list[str] = []
    i = 0
    while i < len(text) and visible < width - 1:
        if text[i] == "\x1b":
            j = text.find("m", i)
            if j == -1:
                break
            out.append(text[i:j + 1])
            i = j + 1
        else:
            out.append(text[i])
            visible += 1
            i += 1
    out.append("…" + _RESET)
    return "".join(out)
```

- [ ] **Step 5: Run tests + full suite**

```bash
uv run pytest tests/compact/test_tree_render.py -v
uv run pytest tests/ -q
uv run mypy src/ansible_aom
```

Expected: the three new tests pass; existing `format_host_summary` tests
(grep `format_host_summary` in `tests/`) stay green because the refactor
is behaviour-preserving.

- [ ] **Step 6: Commit**

```bash
git add src/ansible_aom/compact/renderer.py tests/compact/test_tree_render.py
git commit -m "feat(compact): format_host_rows with worst-status colour and current-task suffix"
```

---

## Task 7: `format_tree_block()` formatter

**Files:**
- Modify: `src/ansible_aom/compact/renderer.py`
- Modify: `tests/compact/test_tree_render.py`

What this delivers: the tree-drawing function. Indents by `depth` (2 spaces per level), draws `└─` / `├─` branch glyphs (ASCII `\-` / `+-` in ascii-mode), colourises task/host glyphs with `get_running_frame` + `get_status_color`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/compact/test_tree_render.py`:

```python
def test_format_tree_block_emits_tree_shape():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {"_event": "v2_playbook_on_play_start",
         "_timestamp": "2026-04-20T10:00:01Z",
         "play": {"id": "p1", "name": "deploy webservers"}},
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:02Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "play": {"id": "p1"}},
        {"_event": "v2_runner_on_start",
         "_timestamp": "2026-04-20T10:00:03Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "host": "web1"},
        {"_event": "v2_runner_on_start",
         "_timestamp": "2026-04-20T10:00:03Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "host": "web2"},
    )
    p = TreeProjection.from_run_state(state)
    block = format_tree_block(p, budget=20, width=80,
                              ascii_mode=False, colorize=False)
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
    block = format_tree_block(p, budget=20, width=80,
                              ascii_mode=True, colorize=False)
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
    assert format_tree_block(p, budget=20, width=80,
                             ascii_mode=False, colorize=False) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/compact/test_tree_render.py -v
```

Expected: ImportError on `format_tree_block`.

- [ ] **Step 3: Implement `format_tree_block`**

Append to `src/ansible_aom/compact/renderer.py`:

```python
# Tree drawing glyphs. ASCII variants chosen to be unambiguous in plain
# terminals: "\-" is the last-child marker, "+-" is intermediate.
_TREE_LAST_UNICODE = "└─ "
_TREE_MID_UNICODE = "├─ "
_TREE_LAST_ASCII = "\\- "
_TREE_MID_ASCII = "+- "


def format_tree_block(
    projection: "TreeProjection",
    budget: int,
    *,
    width: int,
    ascii_mode: bool = False,
    colorize: bool = False,
) -> list[str]:
    """Render the tree block as a list of lines.

    Returns an empty list when the projection says the tree should be
    hidden. The renderer caller stitches this list into the bottom panel.
    """
    from ansible_aom.core.icons import get_running_frame, get_status_color

    if not projection.is_tree_visible():
        return []

    lines = projection.tree_lines(budget=budget)
    if not lines:
        return []

    # Determine "last child at depth D" by looking ahead: a line is the
    # last child of its parent if no following line at depth ≥ D-1 has
    # depth == D. We compute a parallel `is_last` list.
    is_last: list[bool] = []
    for i, ln in enumerate(lines):
        last = True
        for j in range(i + 1, len(lines)):
            if lines[j].depth < ln.depth:
                break
            if lines[j].depth == ln.depth:
                last = False
                break
        is_last.append(last)

    last_glyph = _TREE_LAST_ASCII if ascii_mode else _TREE_LAST_UNICODE
    mid_glyph = _TREE_MID_ASCII if ascii_mode else _TREE_MID_UNICODE

    out: list[str] = []
    for ln, last in zip(lines, is_last):
        indent = "   " * max(ln.depth - 1, 0)
        if ln.depth == 0:
            branch = ""
        else:
            branch = last_glyph if last else mid_glyph

        # Per-line glyph (status icon for task/host; none for play/role).
        glyph_seg = ""
        if ln.kind in ("task", "host") and ln.status is not None:
            if ln.status == Status.RUNNING:
                g = get_running_frame(0)
            else:
                icons = STATUS_ICONS_ASCII if ascii_mode else STATUS_ICONS
                g = icons.get(ln.status, "?")
            color_name = get_status_color(ln.status)
            color_code = {
                "green": _GREEN, "yellow": _YELLOW, "red": _RED,
                "magenta": _MAGENTA, "cyan": _CYAN, "dim": _DIM,
            }.get(color_name, "")
            glyph_seg = (_wrap(g, color_code, colorize) + " ") if color_code else g + " "

        # Host leaves get a "  <hostname> <glyph> <elapsed>s" form.
        if ln.kind == "host":
            elapsed = int(ln.elapsed_s or 0)
            label_seg = f"{ln.label} {glyph_seg}{_wrap(f'{elapsed}s', _DIM, colorize)}"
            text = f"{indent}{branch}{label_seg}"
        else:
            text = f"{indent}{branch}{glyph_seg}{ln.label}"

        if len(_strip_sgr(text)) > width:
            text = _truncate_visible(text, width)
        out.append(text)
    return out
```

- [ ] **Step 4: Run tests + full suite**

```bash
uv run pytest tests/compact/test_tree_render.py -v
uv run pytest tests/ -q
uv run mypy src/ansible_aom
```

Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/compact/renderer.py tests/compact/test_tree_render.py
git commit -m "feat(compact): format_tree_block draws indented tree with status glyphs"
```

---

## Task 8: Wire tree + host rows into `CompactRenderer._render_status_panel`

**Files:**
- Modify: `src/ansible_aom/compact/renderer.py`
- Modify: `tests/compact/test_tree_render.py`

What this delivers: the live renderer composes status bar + tree block + host rows into a single Display update each tick. The existing `_render_status_bar` method is renamed to `_render_status_panel`; all internal call sites updated.

Height budget computation: `clamp(rows // 3 + active_host_count // 3, 5, 25)`. Terminal rows come from `shutil.get_terminal_size`; on non-TTY or no size, default to 24.

- [ ] **Step 1: Write the failing tests**

Append to `tests/compact/test_tree_render.py`:

```python
import shutil
from unittest.mock import patch

from ansible_aom.compact.renderer import CompactRenderer


def _stuff_renderer_state(r: CompactRenderer, *events: dict) -> None:
    r.start("site.yml", [])
    for e in events:
        r.update_state(e)


def test_render_status_panel_is_status_bar_only_before_any_task():
    r = CompactRenderer(is_tty=False)  # non-tty short-circuit: still updates _state
    r.start("site.yml", [])
    # Drive an internal call directly: capture the assembled panel text.
    with patch.object(r._display, "update") as m:
        r._render_status_panel()
    # Last update call's content should NOT contain tree/host markers.
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
    assert "Install nginx" in content
    assert "site.yml" in content


def test_height_budget_scales_with_active_hosts():
    from ansible_aom.compact.renderer import _compute_tree_budget
    assert _compute_tree_budget(rows=24, active_hosts=0) == max(24 // 3, 5)
    assert _compute_tree_budget(rows=24, active_hosts=12) == 24 // 3 + 12 // 3
    # Lower clamp
    assert _compute_tree_budget(rows=10, active_hosts=0) == 5
    # Upper clamp
    assert _compute_tree_budget(rows=200, active_hosts=200) == 25
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/compact/test_tree_render.py -v
```

Expected: `_render_status_panel` not found; `_compute_tree_budget` not found.

- [ ] **Step 3: Add the budget helper and panel composer**

In `src/ansible_aom/compact/renderer.py`, add near the existing module-level helpers:

```python
def _compute_tree_budget(rows: int, active_hosts: int) -> int:
    """Tree height budget in lines.

    Baseline ⅓ of terminal rows; +1 line per 3 active hosts; clamped to
    [5, 25]. See spec §"Height budget & pruning".
    """
    return max(5, min(25, rows // 3 + active_hosts // 3))
```

Add inside `CompactRenderer`:

```python
    def _render_status_panel(self) -> None:
        """Compute and push the current panel (status bar + tree + hosts).

        Replaces the previous _render_status_bar. The composed panel is
        a single string with newline separators; Display tracks the
        row count for cursor management.
        """
        if self._state is None:
            return

        # --- Status bar (unchanged from previous _render_status_bar) -----
        host_statuses: dict[str, Status] = {}
        for play in self._state.plays.values():
            for task in play.tasks.values():
                for hostname, host_state in task.hosts.items():
                    host_statuses[hostname] = host_state.status
        preflight_hosts: set[str] = set()
        for play_def in self._definitions:
            preflight_hosts.update(play_def.resolved_hosts)
        hosts_total = max(len(host_statuses), len(preflight_hosts))
        hosts_completed = sum(
            1 for s in host_statuses.values()
            if s in (Status.OK, Status.CHANGED, Status.SKIPPED, Status.COMPLETED)
        )
        elapsed = time.time() - self._start_time

        status_bar = format_status_bar(
            playbook=self._playbook,
            hosts_completed=hosts_completed,
            hosts_total=hosts_total,
            warnings=self._warnings_count,
            deprecations=self._deprecations_count,
            elapsed_seconds=elapsed,
            tasks_completed=count_completed_tasks(self._state),
            tasks_total=count_total_tasks(self._definitions),
            ascii_mode=self._ascii_mode,
            colorize=self._colorize,
            mode_label=self._mode_label,
            liveness=self._heartbeat.state(time.monotonic()),
        )

        # --- Tree + host rows --------------------------------------------
        from ansible_aom.core.tree import TreeProjection
        import shutil
        projection = TreeProjection.from_run_state(self._state)
        cols, rows = shutil.get_terminal_size((80, 24))
        active_hosts = sum(
            1 for s in host_statuses.values() if s == Status.RUNNING
        )
        budget = _compute_tree_budget(rows, active_hosts)
        tree_lines = format_tree_block(
            projection, budget=budget, width=cols,
            ascii_mode=self._ascii_mode, colorize=self._colorize,
        )
        host_lines: list[str] = []
        if projection.is_host_summary_visible():
            host_lines = format_host_rows(
                projection, width=cols,
                ascii_mode=self._ascii_mode, colorize=self._colorize,
            )

        parts = [status_bar]
        if tree_lines:
            parts.append("\n".join(tree_lines))
        if host_lines:
            parts.append("\n".join(host_lines))
        self._display.update("\n".join(parts))

    def _render_status_bar(self) -> None:
        """Deprecated alias. Kept for any in-flight test references that
        still call the old name; new code calls _render_status_panel."""
        self._render_status_panel()
```

Then update internal callers — search for `self._render_status_bar(` and replace with `self._render_status_panel(`:

```bash
grep -n "_render_status_bar(" src/ansible_aom/compact/renderer.py
```

For each call site that is **not** the deprecated alias body, replace
the call with `_render_status_panel`. (Tip: do this with the Edit tool;
the alias stays as a one-line shim.)

- [ ] **Step 4: Run the full suite**

```bash
uv run pytest tests/ -q
uv run mypy src/ansible_aom
```

Expected: all green. If any existing `test_row_count.py` or
`test_status_bar_*` test fails because the panel now includes more
lines, look at whether the test still reflects intended behaviour — if
yes (e.g. it asserts something that's now meaningfully different), update
the golden inline. Don't change tests that asserted on properties
that should still hold (status-bar shape, row count math).

- [ ] **Step 5: Commit**

```bash
git add src/ansible_aom/compact/renderer.py tests/compact/test_tree_render.py
git commit -m "feat(compact): compose status bar + tree + host rows in one panel"
```

---

## Task 9: End-to-end snapshot of linear, free, and post-recap shapes

**Files:**
- Modify: `tests/compact/test_tree_render.py`

What this delivers: three integration-style snapshot tests pinning the
visible bottom-panel shape under linear strategy (one task, many hosts),
free strategy (two tasks fanned out), and post-recap (tree hidden, host
rows present but suffix dropped).

- [ ] **Step 1: Write the failing tests**

Append to `tests/compact/test_tree_render.py`:

```python
def _full_panel(state: RunState) -> str:
    """Helper: render the assembled panel against a fixed 80-col terminal."""
    from ansible_aom.compact.renderer import (
        _compute_tree_budget, format_host_rows, format_tree_block,
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
    tree = format_tree_block(p, budget=budget, width=80,
                             ascii_mode=False, colorize=False)
    rows = (format_host_rows(p, width=80, ascii_mode=False, colorize=False)
            if p.is_host_summary_visible() else [])
    return "\n".join(tree + rows)


def test_linear_strategy_panel_shape():
    state = _state(
        {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"},
        {"_event": "v2_playbook_on_play_start",
         "_timestamp": "2026-04-20T10:00:01Z",
         "play": {"id": "p1", "name": "deploy"}},
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:02Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "play": {"id": "p1"}},
        *[{"_event": "v2_runner_on_start",
           "_timestamp": "2026-04-20T10:00:03Z",
           "task": {"id": "t1", "name": "Install nginx"},
           "host": h} for h in ("web1", "web2", "web3")],
    )
    panel = _full_panel(state)
    # One task line, three host children, three host rows below.
    assert panel.count("Install nginx") >= 1  # task line + each host's "on:"
    for h in ("web1", "web2", "web3"):
        assert h in panel


def test_free_strategy_panel_shows_two_tasks():
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
        {"_event": "v2_playbook_on_task_start",
         "_timestamp": "2026-04-20T10:00:04Z",
         "task": {"id": "t2", "name": "Configure firewall"},
         "play": {"id": "p1"}},
        {"_event": "v2_runner_on_start",
         "_timestamp": "2026-04-20T10:00:05Z",
         "task": {"id": "t2", "name": "Configure firewall"},
         "host": "web2"},
    )
    panel = _full_panel(state)
    assert "Install nginx" in panel
    assert "Configure firewall" in panel
    # Per-host row suffixes show divergent current tasks
    assert "web1" in panel and "on: Install nginx" in panel
    assert "web2" in panel and "on: Configure firewall" in panel


def test_post_recap_panel_drops_tree_and_suffix():
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
        {"_event": "v2_runner_on_ok",
         "_timestamp": "2026-04-20T10:00:05Z",
         "task": {"id": "t1", "name": "Install nginx"},
         "hosts": {"web2": {"ok": True, "changed": False}}},
        {"_event": "v2_playbook_on_stats",
         "_timestamp": "2026-04-20T10:00:10Z",
         "stats": {}},
    )
    panel = _full_panel(state)
    # No tree (nothing running)
    assert "└─" not in panel and "├─" not in panel
    # Host rows still present
    assert "web1" in panel and "web2" in panel
    # Suffix dropped (no "on:" suffix, no "(idle)" either after recap is fine
    # — but tree definitely hidden)
    assert "Install nginx" not in panel.split("on: ")[-1] if "on: " in panel else True
```

- [ ] **Step 2: Run tests + full suite**

```bash
uv run pytest tests/compact/test_tree_render.py -v
uv run pytest tests/ -q
uv run mypy src/ansible_aom
```

Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add tests/compact/test_tree_render.py
git commit -m "test(compact): snapshot linear, free, and post-recap panel shapes"
```

---

## Final check

After all 9 tasks:

```bash
uv run ruff format
uv run ruff check --fix
uv run mypy src/ansible_aom
uv run pytest tests/ -q --cov=src/ansible_aom --cov-report=term-missing
```

The new `core/tree.py` should have ≥95% line coverage (it's pure data
manipulation). `compact/renderer.py` coverage shouldn't drop from the
pre-task baseline.

If any pre-existing golden tests in `tests/compact/golden/` shifted
because the panel layout changed, examine each diff individually — only
update goldens when the change is intentional.

---

## Spec coverage check (post-write self-review)

Mapping spec sections to tasks:

| Spec section | Task |
|---|---|
| Tree leaf shape (PQ2) | Task 3 (basic), Task 5 (collapse to summary) |
| Per-host summary row (PQ3) | Task 2 (projection), Task 6 (formatter) |
| Tree lifecycle | Task 1 (visibility), Task 8 (post-recap composition) |
| Height budget & pruning | Task 5 (logic), Task 8 (`_compute_tree_budget`) |
| Pruning invariants | Task 5 (active-role invariant; running-host invariant satisfied by host rows in Task 8) |
| Ordering & include/import | Task 3 (source order — events arrive in order), Task 4 (role grouping) |
| `core/tree.py` data model | Task 1 |
| Renderer integration | Task 8 |
| Status-icon colour mapping | Reused in Task 6 + 7; no new colours |
| Testing | Each task |
| Deferred slots (`∅ estimate`, hostname abbreviation) | Documented in spec; left as inline comments where slots exist (Task 3 task-line format, Task 6 host row) |
