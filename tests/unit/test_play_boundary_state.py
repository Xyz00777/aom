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
