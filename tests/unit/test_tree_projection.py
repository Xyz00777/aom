"""Pure-data tests for core/tree.TreeProjection.

The projection is a deterministic function of RunState; tests build a
RunState by firing events from conftest fixtures through handle_event,
then assert on the projection.
"""

from __future__ import annotations

from ansible_aom.core.models import RunState, Status
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
