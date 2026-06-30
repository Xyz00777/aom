# pyright: reportMissingImports=false
"""Boundary regression tests for play transitions in ansible_aom.core.models."""

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


def _ts(minute: int, second: int) -> str:
    return (
        datetime(2026, 5, 23, 10, minute, second, tzinfo=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _task_def(name: str, play_id: str, task_order: int) -> TaskDefinition:
    return TaskDefinition(
        name=name,
        role=None,
        tags=[],
        play_id=play_id,
        play_order=0,
        task_order=task_order,
    )


def _two_play_state() -> RunState:
    state = RunState(playbook="test.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="play one",
            hosts="all",
            resolved_hosts=["host1"],
            tasks=[
                _task_def("Task 1", "1", 0),
                _task_def("Task 2", "1", 1),
            ],
        ),
        PlayDefinition(
            id="2",
            name="play two",
            hosts="all",
            resolved_hosts=["host1"],
            tasks=[_task_def("Next task", "2", 0)],
        ),
    ]
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": _ts(0, 0)})
    return state


def _start_play(state: RunState, play_id: str, name: str, minute: int, second: int) -> None:
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": _ts(minute, second),
            "play": {"id": play_id, "name": name},
        }
    )


def _start_task(
    state: RunState, play_id: str, task_id: str, name: str, minute: int, second: int
) -> None:
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": _ts(minute, second),
            "task": {"id": task_id, "name": name},
            "play": {"id": play_id},
        }
    )


def _runner_ok(
    state: RunState, play_id: str, task_id: str, name: str, minute: int, second: int
) -> None:
    state.handle_event(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": _ts(minute, second),
            "task": {"id": task_id, "name": name},
            "play": {"id": play_id},
            "hosts": {"host1": {"ok": True, "changed": False}},
        }
    )


def _runner_start(state: RunState, play_id: str, task_id: str, name: str, host: str) -> None:
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": _ts(0, 5),
            "task": {"id": task_id, "name": name},
            "play": {"id": play_id},
            "host": host,
        }
    )


class TestPlayBoundaryState:
    def test_same_play_id_replacement_keeps_tasks(self):
        """TC-BOUNDARY-1: Duplicate play_start for the same play_id must not
        destroy already completed runtime tasks."""
        state = _two_play_state()

        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        _runner_ok(state, "play-1", "uuid-task-1", "Task 1", 0, 3)
        _start_task(state, "play-1", "uuid-task-2", "Task 2", 0, 4)
        _runner_ok(state, "play-1", "uuid-task-2", "Task 2", 0, 5)

        _start_play(state, "play-2", "play two", 1, 0)
        assert set(state.plays["play-1"].tasks) == {"uuid-task-1", "uuid-task-2"}

        _start_play(state, "play-1", "play one", 1, 1)

        play = state.plays["play-1"]
        assert set(play.tasks) == {"uuid-task-1", "uuid-task-2"}
        assert play.tasks["uuid-task-1"].status == Status.COMPLETED
        assert play.tasks["uuid-task-2"].status == Status.COMPLETED

    def test_same_play_id_replace_keeps_completed_count(self):
        """TC-BOUNDARY-2: Re-emitting the same play_start must preserve the
        task count already accumulated for that play."""
        state = _two_play_state()

        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        _runner_ok(state, "play-1", "uuid-task-1", "Task 1", 0, 3)
        _start_task(state, "play-1", "uuid-task-2", "Task 2", 0, 4)
        _runner_ok(state, "play-1", "uuid-task-2", "Task 2", 0, 5)
        _start_play(state, "play-2", "play two", 1, 0)

        original_task_ids = set(state.plays["play-1"].tasks)
        assert len(original_task_ids) == 2

        _start_play(state, "play-1", "play one", 1, 1)

        play = state.plays["play-1"]
        assert len(play.tasks) >= len(original_task_ids)
        assert original_task_ids <= set(play.tasks)

    def test_meta_task_force_completed_across_plays(self):
        """TC-BOUNDARY-3: A RUNNING meta task from play 1 must be force-
        completed when play 2 begins its first task, even before any later
        cleanup can catch up."""
        state = _two_play_state()

        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-meta", "Reset connection", 0, 2)

        meta_task = state.plays["play-1"].tasks["uuid-meta"]
        assert meta_task.status == Status.RUNNING
        assert meta_task.hosts["host1"].status == Status.RUNNING

        _start_task(state, "play-2", "uuid-next", "Next task", 1, 0)

        assert meta_task.status == Status.COMPLETED
        assert meta_task.hosts["host1"].status == Status.OK

    def test_cross_play_graft_cursor_resets_on_play_boundary(self):
        """TC-BOUNDARY-4: The dynamic-graft cursor ``_last_matched_task_def``
        must reset to ``None`` when a new play starts. Otherwise an unknown
        task arriving between the new play_start and the new play's first
        matched task gets grafted onto the PRIOR play's last preflight task,
        polluting the new play's tree (and growing the prior play's
        definition's children list).
        """
        state = _two_play_state()

        # Play 1: Task 1 matches preflight → cursor = "Task 1"
        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        assert state._last_matched_task_def is not None
        assert state._last_matched_task_def.name == "Task 1"

        # Play 2 starts — cursor must reset to None here.
        _start_play(state, "play-2", "play two", 0, 3)
        assert state._last_matched_task_def is None

        # Unknown task arrives BEFORE the first matched preflight task of
        # play 2 (e.g. a dynamic include_tasks child whose parent hasn't
        # been task_start'd yet). It must be left as an orphan, NOT
        # grafted onto the play 1 preflight definition.
        play1_preflight_task = state.definitions[0].tasks[0]
        assert play1_preflight_task.children == []
        _start_task(state, "play-2", "uuid-unknown", "Unknown inner task", 0, 4)

        # The prior play's preflight task must NOT have grown children
        # (the bug grafted the unknown task here).
        assert play1_preflight_task.children == []

        # The unknown task must still land in play-2's runtime tasks
        # (it has a play_id so it belongs there).
        assert "uuid-unknown" in state.plays["play-2"].tasks

        # And it must NOT have been added to play-1's runtime tasks.
        assert "uuid-unknown" not in state.plays["play-1"].tasks

        # Now play 2's first matched preflight task arrives and updates
        # the cursor — the cursor must reflect the new play.
        _start_task(state, "play-2", "uuid-next", "Next task", 0, 5)
        assert state._last_matched_task_def is not None
        assert state._last_matched_task_def.name == "Next task"

    def test_free_strategy_prior_play_not_force_finalised(self):
        """TC-BOUNDARY-5: Under ``strategy: free`` a play_start for play N
        can arrive while play N-1's hosts are still running their tasks
        (ansible-core 2.16+ emits the next play_start eagerly under free
        strategy). Force-finalising play N-1 on the play_start boundary
        would mark its RUNNING hosts as OK, destroying live state and
        producing a stale "all green" tree.
        """
        state = _two_play_state()

        # Play 1 starts — task_start alone sets strategy to "linear".
        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        assert state.plays["play-1"].detected_strategy == "linear"

        # runner_on_start flips the detected strategy to "free" — the
        # playbook is not running lockstep.
        _runner_start(state, "play-1", "uuid-task-1", "Task 1", "host1")
        assert state.plays["play-1"].detected_strategy == "free"
        assert state.plays["play-1"].tasks["uuid-task-1"].hosts["host1"].status == Status.RUNNING

        # Play 2 starts while play 1's host is still RUNNING. Under the
        # fixed code, play 1 must NOT be force-finalised.
        _start_play(state, "play-2", "play two", 0, 3)

        play_1 = state.plays["play-1"]
        assert play_1.status != Status.COMPLETED, (
            "Play 1 must remain non-completed under strategy: free — "
            "its hosts may still be running tasks when play 2 starts."
        )
        # Host must still be RUNNING — force-finalisation would have
        # flipped it to OK.
        assert play_1.tasks["uuid-task-1"].hosts["host1"].status == Status.RUNNING

    def test_linear_strategy_prior_play_still_force_finalised(self):
        """TC-BOUNDARY-6: The free-strategy skip must NOT regress the linear
        case — a play_start for the next play is still proof that the
        previous play is done under lockstep, so prior plays must be
        force-finalised as before.
        """
        state = _two_play_state()

        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        # No v2_runner_on_start → strategy stays "linear".
        assert state.plays["play-1"].detected_strategy == "linear"
        assert state.plays["play-1"].tasks["uuid-task-1"].hosts["host1"].status == Status.RUNNING

        _start_play(state, "play-2", "play two", 0, 3)

        play_1 = state.plays["play-1"]
        assert play_1.status == Status.COMPLETED
        # Under linear strategy, RUNNING hosts ARE force-finalised to OK
        # (the long-standing pause-lingering fix).
        assert play_1.tasks["uuid-task-1"].hosts["host1"].status == Status.OK

    def test_runner_events_route_to_task_owner_play(self):
        """TC-BOUNDARY-7: A ``v2_runner_on_*`` event that arrives WITHOUT a
        ``play`` field must route to the play that already owns the
        task_id, NOT to ``_current_play_id``.

        Regression: under ``strategy: free`` the next play's
        ``v2_playbook_on_play_start`` can arrive while the previous play's
        runner events are still streaming in. Trusting the cursor
        (``_current_play_id``) routed those events to the wrong play,
        polluting the next play's task list and producing a tree view
        that showed the wrong tasks as "pending ahead".
        """
        state = _two_play_state()

        # Play 1 starts and its first task is task_started.
        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)

        # Play 2's play_start advances the cursor before play 1's runner
        # events have landed — exactly the late-event ordering that
        # produced the mis-routing bug.
        _start_play(state, "play-2", "play two", 0, 3)

        # runner_on_start WITHOUT a play field. task.id is uuid-task-1,
        # which already belongs to play-1.
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": _ts(0, 4),
                "task": {"id": "uuid-task-1", "name": "Task 1"},
                "host": "host1",
            }
        )

        # The task must stay in play-1 (where task_start put it).
        assert "uuid-task-1" in state.plays["play-1"].tasks
        # And it must NOT have been grafted onto play-2.
        assert "uuid-task-1" not in state.plays["play-2"].tasks

    def test_terminal_runner_events_route_to_task_owner_play(self):
        """TC-BOUNDARY-8: A terminal ``v2_runner_on_ok`` event that arrives
        WITHOUT a ``play`` field must route to the play that already owns
        the task_id, just like the start event. The fix in
        ``_resolve_play_id`` is shared across all runner handlers, so
        this test guards against regressions in ``_handle_v2_runner_on_ok``
        specifically (the most common terminal event).
        """
        state = _two_play_state()

        _start_play(state, "play-1", "play one", 0, 1)
        _start_task(state, "play-1", "uuid-task-1", "Task 1", 0, 2)
        # First start the task so the host exists and can transition to OK.
        _runner_start(state, "play-1", "uuid-task-1", "Task 1", "host1")

        _start_play(state, "play-2", "play two", 0, 3)

        # Terminal event WITHOUT a play field. The cursor is on play-2,
        # but task uuid-task-1 still belongs to play-1.
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": _ts(0, 4),
                "task": {"id": "uuid-task-1", "name": "Task 1"},
                "hosts": {"host1": {"ok": True, "changed": False}},
            }
        )

        # host1 must be OK in play-1 (the ok event landed in the right place).
        play_1 = state.plays["play-1"]
        assert play_1.tasks["uuid-task-1"].hosts["host1"].status == Status.OK
        # And play-2 must have no record of this task.
        assert "uuid-task-1" not in state.plays["play-2"].tasks
