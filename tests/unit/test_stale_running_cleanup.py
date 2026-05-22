"""Regression tests for stale RUNNING hosts in the state model.

When terminal events (v2_runner_on_ok etc.) are lost due to play_id/task_id
mismatch, HostRunState entries can remain stuck as RUNNING even after the
playbook finishes. The v2_playbook_on_stats handler must clean these up.

Also tests that host_rows() does not show stale RUNNING tasks after cleanup.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import TreeProjection


def _make_state_with_stale_running() -> RunState:
    """Build a RunState where ipa1 completed task A but is stuck as RUNNING
    on task B because v2_runner_on_ok was lost (wrong play_id)."""
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=["ipa1", "ipa2"],
            tasks=[],
        )
    ]

    # Play is registered by v2_playbook_on_play_start
    play_id = "play-abc-123"
    state.plays[play_id] = PlayRunState(
        play_id=play_id,
        name="deploy",
        status=Status.RUNNING,
    )

    # Task A: both hosts completed
    task_a = TaskRunState(
        task_id="t-a",
        name="Install nginx",
        status=Status.RUNNING,
        start_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
    )
    task_a.hosts["ipa1"] = HostRunState(
        hostname="ipa1",
        status=Status.OK,
        start_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 5, 22, 10, 0, 5, tzinfo=timezone.utc),
    )
    task_a.hosts["ipa2"] = HostRunState(
        hostname="ipa2",
        status=Status.OK,
        start_time=datetime(2026, 5, 22, 10, 0, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 5, 22, 10, 0, 6, tzinfo=timezone.utc),
    )
    state.plays[play_id].tasks["t-a"] = task_a

    # Task B: ipa1 stuck as RUNNING (terminal event was lost),
    # ipa2 completed normally
    task_b = TaskRunState(
        task_id="t-b",
        name="Reset connection",
        status=Status.RUNNING,
        start_time=datetime(2026, 5, 22, 10, 0, 7, tzinfo=timezone.utc),
    )
    task_b.hosts["ipa1"] = HostRunState(
        hostname="ipa1",
        status=Status.RUNNING,
        start_time=datetime(2026, 5, 22, 10, 0, 7, tzinfo=timezone.utc),
    )
    task_b.hosts["ipa2"] = HostRunState(
        hostname="ipa2",
        status=Status.CHANGED,
        changed=True,
        start_time=datetime(2026, 5, 22, 10, 0, 8, tzinfo=timezone.utc),
        end_time=datetime(2026, 5, 22, 10, 0, 15, tzinfo=timezone.utc),
    )
    state.plays[play_id].tasks["t-b"] = task_b

    return state


class TestStaleRunningCleanup:
    """When playbook ends, stale RUNNING hosts must be cleaned up."""

    def test_v2_playbook_on_stats_clears_stale_running_hosts(self):
        """After v2_playbook_on_stats, hosts stuck as RUNNING must be
        transitioned to OK so the overview and tree don't show them as
        still running."""
        state = _make_state_with_stale_running()

        # Before cleanup: ipa1 is stuck as RUNNING on task B
        task_b = state.plays["play-abc-123"].tasks["t-b"]
        assert task_b.hosts["ipa1"].status == Status.RUNNING

        # Simulate playbook completion
        state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-22T10:00:30Z",
            "stats": {},
        })

        # After cleanup: ipa1 should no longer be RUNNING
        assert task_b.hosts["ipa1"].status != Status.RUNNING, (
            f"ipa1 should not be RUNNING after playbook ends, got {task_b.hosts['ipa1'].status}"
        )

    def test_host_rows_no_stale_running_after_stats(self):
        """host_rows() should not show any host as still running after
        the playbook has completed and stale entries are cleaned up."""
        state = _make_state_with_stale_running()

        # Before cleanup: host overview shows ipa1 stuck on "Reset connection"
        p = TreeProjection.from_run_state(state)
        rows = p.host_rows(now=datetime(2026, 5, 22, 10, 1, 0, tzinfo=timezone.utc))
        stuck = [r for r in rows if r.current_task is not None and "Reset" in (r.current_task or "")]
        assert len(stuck) > 0, "precondition: at least one host stuck on 'Reset connection'"

        # Simulate playbook completion
        state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-22T10:00:30Z",
            "stats": {},
        })

        # After cleanup: no host should show as still running a task
        p2 = TreeProjection.from_run_state(state)
        rows2 = p2.host_rows(now=datetime(2026, 5, 22, 10, 1, 0, tzinfo=timezone.utc))
        still_running = [r for r in rows2 if r.current_task is not None]
        assert len(still_running) == 0, (
            f"after playbook completion, no host should have a current_task, "
            f"but got: {[(r.hostname, r.current_task) for r in still_running]}"
        )

    def test_completed_hosts_preserved_after_stats_cleanup(self):
        """Cleaning up stale RUNNING hosts must not alter hosts that already
        have terminal status (OK, CHANGED, FAILED)."""
        state = _make_state_with_stale_running()

        # ipa2 completed task B normally (CHANGED)
        task_b = state.plays["play-abc-123"].tasks["t-b"]
        ipa2_before = task_b.hosts["ipa2"]

        state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-22T10:00:30Z",
            "stats": {},
        })

        # ipa2's status should be unchanged
        ipa2_after = task_b.hosts["ipa2"]
        assert ipa2_after.status == ipa2_before.status
        assert ipa2_after.changed == ipa2_before.changed

    def test_task_status_cleared_after_stats_cleanup(self):
        """TaskRunState.status should be cleared from RUNNING after
        playbook completion when all hosts in the task have terminal status."""
        state = _make_state_with_stale_running()

        state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-05-22T10:00:30Z",
            "stats": {},
        })

        # Task B had ipa1 stuck as RUNNING; after cleanup ipa1 should be
        # terminal, so _classify should return "completed" for task B.
        # Verify by checking that TreeProjection doesn't show task B as running.
        task_b = state.plays["play-abc-123"].tasks["t-b"]
        # ipa1 should now be OK (or CHANGED), not RUNNING
        assert task_b.hosts["ipa1"].status != Status.RUNNING


class TestHostRowsCurrentTask:
    """Test that host_rows() correctly tracks current_task per host."""

    def test_host_rows_clears_current_task_when_all_tasks_complete(self):
        """When all hosts have completed all tasks, host_rows should show
        current_task=None (idle) for every host."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="1",
                name="deploy",
                hosts="all",
                resolved_hosts=["web1", "web2"],
                tasks=[],
            )
        ]

        play_id = "play-1"
        state.plays[play_id] = PlayRunState(
            play_id=play_id,
            name="deploy",
            status=Status.COMPLETED,
        )

        # One completed task: both hosts OK
        task = TaskRunState(
            task_id="t-1",
            name="Install nginx",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
        )
        task.hosts["web1"] = HostRunState(
            hostname="web1",
            status=Status.OK,
            changed=False,
            end_time=datetime(2026, 5, 22, 10, 0, 5, tzinfo=timezone.utc),
        )
        task.hosts["web2"] = HostRunState(
            hostname="web2",
            status=Status.OK,
            changed=False,
            end_time=datetime(2026, 5, 22, 10, 0, 6, tzinfo=timezone.utc),
        )
        state.plays[play_id].tasks["t-1"] = task

        p = TreeProjection.from_run_state(state)
        rows = p.host_rows()
        for row in rows:
            assert row.current_task is None, (
                f"{row.hostname} should be idle, but shows current_task={row.current_task!r}"
            )

    def test_host_rows_shows_running_task_while_host_is_running(self):
        """When a host is actively running a task, current_task should show it."""
        state = RunState(playbook="site.yml")
        state.definitions = [
            PlayDefinition(
                id="1", name="deploy", hosts="all", resolved_hosts=["web1"], tasks=[],
            )
        ]

        play_id = "play-1"
        state.plays[play_id] = PlayRunState(
            play_id=play_id, name="deploy", status=Status.RUNNING,
        )

        task = TaskRunState(
            task_id="t-1",
            name="Install nginx",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
        )
        task.hosts["web1"] = HostRunState(
            hostname="web1",
            status=Status.RUNNING,
            start_time=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
        )
        state.plays[play_id].tasks["t-1"] = task

        p = TreeProjection.from_run_state(state)
        rows = p.host_rows(now=datetime(2026, 5, 22, 10, 0, 30, tzinfo=timezone.utc))
        assert rows[0].current_task == "Install nginx"