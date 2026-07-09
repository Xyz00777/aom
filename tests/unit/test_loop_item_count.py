"""Per-host loop item counting for the TUI task tree.

The bundled ``aom_jsonl`` callback emits one ``v2_runner_item_on_*`` event
per loop iteration. RunState tallies these per host so the tree row can
show a live ``(N items)`` count while the loop runs. The tally must NOT
touch status counts — the host stays RUNNING until the aggregate
``v2_runner_on_*`` lands and decides the real outcome.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.models import Status
from ansible_aom.core.run_state import RunState
from ansible_aom.core.tree import TreeProjection


def _item_event(host: str, label: str, *, ts: str = "2026-04-20T10:00:03Z") -> dict:
    return {
        "_event": "v2_runner_item_on_ok",
        "_timestamp": ts,
        "task": {"id": "task-uuid-1", "name": "Install nginx"},
        "hosts": {host: {"_ansible_item_label": label, "changed": False}},
    }


def _running_loop_state(
    event_playbook_start, event_play_start, event_task_start, *, items: int = 3
) -> RunState:
    state = RunState(playbook="site.yml")
    for ev in (event_playbook_start, event_play_start, event_task_start):
        state.handle_event(ev)
    for i in range(items):
        state.handle_event(_item_event("web1", f"item{i}"))
    return state


class TestRunStateCounter:
    def test_item_events_increment_per_host_counter(
        self, event_playbook_start, event_play_start, event_task_start
    ):
        state = _running_loop_state(
            event_playbook_start, event_play_start, event_task_start, items=3
        )
        host = state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host.loop_items_done == 3

    def test_item_events_keep_host_running(
        self, event_playbook_start, event_play_start, event_task_start
    ):
        # The loop is still in progress: the host must read RUNNING, not OK.
        state = _running_loop_state(
            event_playbook_start, event_play_start, event_task_start, items=2
        )
        host = state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host.status == Status.RUNNING

    def test_item_events_do_not_inflate_status_counts(
        self, event_playbook_start, event_play_start, event_task_start
    ):
        # Three item events on one host must count as one running host —
        # not three completed hosts.
        state = _running_loop_state(
            event_playbook_start, event_play_start, event_task_start, items=3
        )
        task = state.plays["play-uuid-1"].tasks["task-uuid-1"]
        running = sum(1 for hs in task.hosts.values() if hs.status == Status.RUNNING)
        assert running == 1


class TestTreeRendersCount:
    def test_running_host_leaf_shows_item_count(
        self, event_playbook_start, event_play_start, event_task_start
    ):
        state = _running_loop_state(
            event_playbook_start, event_play_start, event_task_start, items=3
        )
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=50, now=datetime.now(timezone.utc))
        host_lines = [ln for ln in lines if ln.kind == "host" and "web1" in ln.label]
        assert host_lines, f"no host leaf for web1 in {[ln.label for ln in lines]}"
        assert any("(3 items)" in ln.label for ln in host_lines), (
            f"expected '(3 items)' in {[ln.label for ln in host_lines]}"
        )

    def test_running_host_leaf_shows_n_over_total_when_known(
        self, event_playbook_start, event_play_start
    ):
        # A prior run supplied this loop's total (12) via state.loop_totals,
        # keyed by task path, so the row reads "5/12" mid-loop.
        task_start = {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Install nginx", "path": "site.yml:5"},
            "play": {"id": "play-uuid-1"},
        }
        state = RunState(playbook="site.yml")
        for ev in (event_playbook_start, event_play_start, task_start):
            state.handle_event(ev)
        state.loop_totals = {"site.yml:5": {"web1": 12}}
        for i in range(5):
            state.handle_event(_item_event("web1", f"item{i}"))

        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=50, now=datetime.now(timezone.utc))
        host_lines = [ln for ln in lines if ln.kind == "host" and "web1" in ln.label]
        assert host_lines
        assert any("5/12" in ln.label for ln in host_lines), (
            f"expected '5/12' in {[ln.label for ln in host_lines]}"
        )

    def test_no_count_when_no_items(
        self, event_playbook_start, event_play_start, event_task_start, event_runner_start
    ):
        # A plain (non-loop) running task must not gain an item suffix.
        state = RunState(playbook="site.yml")
        for ev in (event_playbook_start, event_play_start, event_task_start, event_runner_start):
            state.handle_event(ev)
        p = TreeProjection.from_run_state(state)
        lines = p.tree_lines(budget=50, now=datetime.now(timezone.utc))
        host_lines = [ln for ln in lines if ln.kind == "host"]
        assert host_lines
        assert all("items)" not in ln.label for ln in host_lines)
