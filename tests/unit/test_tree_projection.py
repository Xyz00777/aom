"""Pure-data tests for core/tree.TreeProjection.

The projection is a deterministic function of RunState; tests build a
RunState by firing events from conftest fixtures through handle_event,
then assert on the projection.
"""

from __future__ import annotations

from ansible_aom.core.models import (
    PlayDefinition,
    RoleGroupDefinition,
    RunState,
    Status,
    TaskDefinition,
)
from ansible_aom.core.tree import HostRow, TreeLine, TreeProjection


def _state_with_running_task(
    event_playbook_start, event_play_start, event_task_start, event_runner_start
) -> RunState:
    state = RunState(playbook="site.yml")
    for ev in (event_playbook_start, event_play_start, event_task_start, event_runner_start):
        state.handle_event(ev)
    return state


class TestVisibility:
    def test_empty_state_hides_everything(self):
        state = RunState(playbook="site.yml")
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False
        assert p.is_host_summary_visible() is False

    def test_running_task_shows_tree(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True

    def test_host_summary_hidden_for_single_host(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        # Only web1 has appeared so far
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is False

    def test_host_summary_visible_for_multi_host(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        state = _state_with_running_task(
            event_playbook_start, event_play_start, event_task_start, event_runner_start
        )
        # Fire a second host on the same task
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "host": "web2",
            }
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_host_summary_visible() is True


class TestDataclassShapes:
    def test_tree_line_is_frozen(self):
        line = TreeLine(
            depth=0,
            kind="task",
            label="Install nginx",
            glyph="◐",
            status=Status.RUNNING,
            elapsed_s=1.0,
        )
        try:
            line.depth = 5  # type: ignore[misc]
        except Exception as e:
            msg = str(e).lower()
            assert "frozen" in msg or "attribute" in msg or "field" in msg
        else:
            raise AssertionError("TreeLine must be frozen")

    def test_host_row_is_frozen(self):
        row = HostRow(
            hostname="web1",
            counts={Status.OK: 3},
            worst_status=Status.OK,
            current_task=None,
            current_elapsed_s=None,
        )
        try:
            row.hostname = "web2"  # type: ignore[misc]
        except Exception as e:
            msg = str(e).lower()
            assert "frozen" in msg or "attribute" in msg or "field" in msg
        else:
            raise AssertionError("HostRow must be frozen")


class TestHostRows:
    def _multi_host_state(self) -> RunState:
        """web1 done-ok, web2 running, web3 done-changed, db1 unreachable."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web3": {"ok": True, "changed": True}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"db1": {"unreachable": True}},
            }
        )
        # web2 is mid-task
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web2",
            }
        )
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

    def test_failed_outranks_changed_in_worst_status(self):
        """FAILED has highest precedence — a single failure dominates worst_status."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "Deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        # web1: one CHANGED task, then one FAILED task
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": True}},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Start service"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Start service"},
                "hosts": {"web1": {"failed": True, "msg": "boom"}},
            }
        )
        p = TreeProjection.from_run_state(state)
        rows = {r.hostname: r for r in p.host_rows()}
        assert rows["web1"].worst_status == Status.FAILED
        assert rows["web1"].counts == {Status.CHANGED: 1, Status.FAILED: 1}


class TestTreeLinesBasic:
    def _running_task_state(self) -> RunState:
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy webservers"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:03Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "host": host,
                }
            )
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
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
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
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        p = TreeProjection.from_run_state(state)
        host_lines = [ln for ln in p.tree_lines(budget=20) if ln.kind == "host"]
        assert [ln.label for ln in host_lines] == ["web2"]

    def test_no_lines_when_no_task_running(self):
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        p = TreeProjection.from_run_state(state)
        assert p.tree_lines(budget=20) == []


class TestTreeLinesRolesAndFanOut:
    def _role_aware_definitions(self) -> list[PlayDefinition]:
        # Mirrors preflight output: one play with one role containing two tasks.
        return [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1", "web2"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                                path="nginx.yml:1",
                            ),
                            TaskDefinition(
                                name="Configure firewall",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=1,
                                path="nginx.yml:5",
                            ),
                        ],
                    ),
                ],
            )
        ]

    def _free_strategy_state(self) -> RunState:
        # `ansible.posix.jsonl` emits v2_playbook_on_task_start ONLY under
        # lockstep strategies (linear/host_pinned) and v2_runner_on_start
        # ONLY under non-lockstep strategies (free). A realistic free-
        # strategy fixture fires runner_on_start without a preceding
        # task_start — one host per concurrent task.
        state = RunState(playbook="site.yml")
        state.definitions = self._role_aware_definitions()
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        # web1 is on "Install nginx"; web2 has raced ahead to "Configure firewall"
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web2",
            }
        )
        return state

    def test_role_branch_appears_above_role_tasks(self):
        state = self._free_strategy_state()
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)

        # Expected ordering: playbook, play, role, task, host, task, host
        kinds_labels = [(ln.kind, ln.label) for ln in lines]
        role_lines = [kl for kl in kinds_labels if kl[0] == "role"]
        assert len(role_lines) >= 1, f"expected at least one role line, got {kinds_labels}"
        # Role labels now include task count (e.g. "role: webserver (2 tasks)")
        assert role_lines[0][1].startswith("role: webserver")
        role_idx = kinds_labels.index(role_lines[0])
        # Tasks under the role have depth > role's depth
        role_depth = lines[role_idx].depth
        # Both task lines should follow the role line with depth > role_depth
        for ln in lines[role_idx + 1 :]:
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


class TestTreeLinesPruning:
    def _many_tasks_state(self, n_roles: int, tasks_per_role: int, hosts_per_task: int) -> RunState:
        """Build a RunState with n_roles × tasks_per_role tasks, each
        running on hosts_per_task hosts. All tasks are concurrent
        (free-strategy-style fan-out) — pruning is exercised by the
        sheer line count.
        """
        state = RunState(playbook="site.yml")
        roles = [
            RoleGroupDefinition(
                role=f"role{r}",
                tasks=[
                    TaskDefinition(
                        name=f"r{r}-t{t}",
                        role=f"role{r}",
                        tags=[],
                        play_id="p1",
                        play_order=0,
                        task_order=t,
                    )
                    for t in range(tasks_per_role)
                ],
            )
            for r in range(n_roles)
        ]
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="big",
                hosts="all",
                resolved_hosts=[f"h{i}" for i in range(hosts_per_task)],
                tasks=list(roles),
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "big"},
            }
        )
        for r in range(n_roles):
            for t in range(tasks_per_role):
                tname = f"r{r}-t{t}"
                state.handle_event(
                    {
                        "_event": "v2_playbook_on_task_start",
                        "_timestamp": "2026-04-20T10:00:02Z",
                        "task": {"id": f"{r}-{t}", "name": tname},
                        "play": {"id": "p1"},
                    }
                )
                for h in range(hosts_per_task):
                    state.handle_event(
                        {
                            "_event": "v2_runner_on_start",
                            "_timestamp": "2026-04-20T10:00:03Z",
                            "task": {"id": f"{r}-{t}", "name": tname},
                            "host": f"h{h}",
                        }
                    )
        return state

    def test_within_budget_is_unchanged(self):
        # Generous budget — no pruning should happen.
        from datetime import datetime, timezone

        state = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        now = datetime(2026, 4, 20, 10, 0, 5, tzinfo=timezone.utc)
        # Within-budget call equals the unbounded baseline.
        bounded = p.tree_lines(budget=999, now=now)
        # Re-fetch with a generous budget — should be deterministic.
        again = p.tree_lines(budget=999, now=now)
        assert bounded == again
        # Sanity check: host leaves present (not pruned away).
        assert any(ln.kind == "host" for ln in bounded)

    def test_collapses_host_leaves_first(self):
        # 1 role × 1 task × 5 hosts → 1 playbook + 1 play + 1 role + 1 task
        # + 5 hosts = 9 lines. Budget 4 fits the structure + task but no hosts;
        # budget 5 fits one host as well (truncate-from-end preserves the
        # active play's depth over upcoming breadth).
        state = self._many_tasks_state(n_roles=1, tasks_per_role=1, hosts_per_task=5)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=4)
        kinds = [ln.kind for ln in lines]
        assert "task" in kinds
        assert "host" not in kinds
        assert len(lines) <= 4

    def test_invariant_one_each_active_role_keeps_one_line(self):
        # 4 roles × 3 tasks × 2 hosts = lots. With a generous budget,
        # every role should be visible. With a tight budget, the
        # truncate-from-end approach prioritizes depth (showing role0's
        # full subtree with hosts) over breadth (showing all 4 roles).
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        # Generous budget: all 4 roles visible.
        lines = p.tree_lines(budget=42)
        labels = "\n".join(ln.label for ln in lines)
        for r in range(4):
            assert f"role{r}" in labels, f"role{r} missing from full output:\n{labels}"

    def test_tight_budget_preserves_depth_over_breadth(self):
        # With a tight budget, truncate-from-end keeps the first role's
        # subtree (role0's tasks + hosts) and cuts later roles entirely.
        state = self._many_tasks_state(n_roles=4, tasks_per_role=3, hosts_per_task=2)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=8)
        labels = "\n".join(ln.label for ln in lines)
        # role0 is always visible (it's first in the tree).
        assert "role0" in labels, f"role0 missing from tight-budget output:\n{labels}"
        # Host leaves from role0's first task are visible (depth preserved).
        assert any(ln.kind == "host" for ln in lines), (
            f"expected host leaves in tight-budget output:\n{labels}"
        )

    def test_collapsed_role_summary_format(self):
        # Force collapse: many hosts so truncation still overflows after
        # dropping hosts. 4 roles × 1 task × 10 hosts = 47 unbounded lines.
        # After dropping hosts (stage b): 7 lines. With budget 5, roles
        # get collapsed (stage c).
        state = self._many_tasks_state(n_roles=4, tasks_per_role=1, hosts_per_task=10)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=5)
        role_summary_lines = [
            ln for ln in lines if ln.kind == "role" and "tasks running" in ln.label
        ]
        # Format check: "role: roleN  (M tasks running on K hosts)"
        for ln in role_summary_lines:
            assert ln.label.startswith("role: role")
            assert "tasks running on" in ln.label
            assert "hosts)" in ln.label


class TestTreeLineIdentity:
    """Regression guard: role TreeLines carry a structured identity field
    so the pruner / renderer don't have to parse `label`."""

    def test_role_line_has_identity_matching_role_name(self):
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="p1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1"],
                tasks=[
                    RoleGroupDefinition(
                        role="webserver",
                        tasks=[
                            TaskDefinition(
                                name="Install nginx",
                                role="webserver",
                                tags=[],
                                play_id="p1",
                                play_order=0,
                                task_order=0,
                            )
                        ],
                    )
                ],
            )
        ]
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        role_line = next(ln for ln in lines if ln.kind == "role")
        assert role_line.identity == "webserver"
        # Label now includes task count
        assert role_line.label.startswith("role: webserver")

    def test_non_role_lines_have_none_identity(self):
        from ansible_aom.core.models import (
            PlayDefinition,
            RoleGroupDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=25)
        for ln in lines:
            if ln.kind != "role":
                assert ln.identity is None, (
                    f"non-role line {ln.kind!r}/{ln.label!r} has non-None identity"
                )


class TestTaskCompletionLifecycle:
    """Regression guards: under linear strategy the state machine sets
    task.status = RUNNING on v2_runner_on_start and never transitions it
    back. The projection therefore must not rely on task.status to decide
    'is this task currently running'; it must derive that from per-host
    HostRunState.RUNNING entries instead. See bug found post-Task 9."""

    def _linear_strategy_finished_task(self) -> RunState:
        """Simulate a complete linear-strategy task lifecycle:
        task_start → runner_on_start per host → runner_on_ok per host.
        After this sequence task.status is stuck at RUNNING but every
        host has terminal status — the task is logically complete."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_start",
                    "_timestamp": "2026-04-20T10:00:03Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "host": host,
                }
            )
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-04-20T10:00:05Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "hosts": {host: {"ok": True, "changed": False}},
                }
            )
        return state

    def test_tree_visible_after_all_hosts_finished_no_stats(self):
        """After a task's hosts all reach terminal state, the tree
        stays visible (sticky) until either the next task starts or
        v2_playbook_on_stats fires. See sister test
        `test_tree_sticky_between_tasks_shows_last_task` and
        `test_tree_hidden_after_playbook_stats` for the bracketing
        cases."""
        state = self._linear_strategy_finished_task()
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True

    def test_tree_does_not_show_completed_task_between_tasks(self):
        """Completed tasks are intentionally dropped from the tree — the
        streaming log above the panel already carries them. Between
        tasks the tree's job is to show pending work, not replay history.
        Regression guard for the post-redesign contract: 'show only the
        currently-running task and everything still to come.'"""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        for host in ("web1", "web2"):
            state.handle_event(
                {
                    "_event": "v2_runner_on_ok",
                    "_timestamp": "2026-04-20T10:00:05Z",
                    "task": {"id": "t1", "name": "Install nginx"},
                    "hosts": {host: {"ok": True, "changed": False}},
                }
            )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is True, (
            "tree should remain visible between tasks while playbook is in flight"
        )
        lines = p.tree_lines(budget=25)
        # No preflight definitions + only completed runtime tasks → the
        # play yields nothing to show. The tree degrades to just the
        # playbook header line until the next task starts.
        assert all(ln.label != "Install nginx" for ln in lines if ln.kind == "task"), lines

    def test_tree_hidden_after_playbook_stats(self):
        """Once v2_playbook_on_stats fires, RunState.status becomes
        COMPLETED/FAILED and end_time is set — the tree should hide
        regardless of any lingering task entries."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True, "changed": False}},
            }
        )
        state.handle_event(
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-04-20T10:00:10Z", "stats": {}}
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False

    def test_tree_hidden_before_any_task_starts(self):
        """At the very start of a run (after playbook_on_start, before
        any task announcement), there's nothing to show. Tree must
        stay hidden — sticky-mode only kicks in once a task has been
        seen."""
        state = RunState(playbook="site.yml")
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "p1", "name": "deploy"},
            }
        )
        p = TreeProjection.from_run_state(state)
        assert p.is_tree_visible() is False

    def test_tree_visible_under_linear_strategy_with_preflight_hosts(self):
        """Under linear strategy, `ansible.posix.jsonl` does NOT emit
        `v2_runner_on_start` (the callback guards it with `if
        self._is_lockstep: return`). So per-host RUNNING entries cannot
        come from runner_on_start. Instead they must be synthesised at
        `v2_playbook_on_task_start` using the matching play's preflight
        `resolved_hosts`. Regression guard for: tree never appearing
        under linear-strategy playbooks."""
        from ansible_aom.core.models import (
            PlayDefinition,
            TaskDefinition,
        )

        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="webservers",
                resolved_hosts=["web1", "web2", "web3"],
                tasks=[
                    TaskDefinition(
                        name="Install nginx",
                        role=None,
                        tags=[],
                        play_id="1",
                        play_order=0,
                        task_order=0,
                    )
                ],
            )
        ]
        # No v2_runner_on_start events — pure linear-strategy flow.
        state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-real", "name": "deploy"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "t1", "name": "Install nginx"},
                "play": {"id": "play-uuid-real"},
            }
        )
        p = TreeProjection.from_run_state(state)
        # The tree must be visible — all three hosts should be reported
        # as RUNNING for this task.
        assert p.is_tree_visible() is True
        host_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "host"]
        host_labels = sorted(ln.label for ln in host_lines)
        assert host_labels == ["web1", "web2", "web3"]

    def test_tree_lines_skip_tasks_with_no_running_hosts(self):
        """A new task starts while a previous task is still stuck at
        task.status=RUNNING but has all hosts in terminal state. The
        tree should show ONLY the new task, not the stale one."""
        state = self._linear_strategy_finished_task()
        state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "play": {"id": "p1"},
            }
        )
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:07Z",
                "task": {"id": "t2", "name": "Configure firewall"},
                "host": "web1",
            }
        )
        p = TreeProjection.from_run_state(state)
        task_lines = [ln for ln in p.tree_lines(budget=25) if ln.kind == "task"]
        names = [ln.label.split("  ")[0] for ln in task_lines]
        assert "Install nginx" not in names, (
            f"completed task should not appear in tree, got {names!r}"
        )
        assert "Configure firewall" in names
