"""R12 — enforce MAX_PLAYS / MAX_TASKS_PER_PLAY / MAX_HOSTS_PER_TASK / MAX_TOTAL_HOST_RUN_STATES.

R12 spec: the four ``MAX_*`` constants in :mod:`ansible_aom.core.state_machine`
were declared (SPECIFICATION.md §6.5) but never enforced. A run that emits
1001 plays, 10001 tasks in one play, 10001 hosts on one task, or 1 000 001
``HostRunState`` entries anywhere in the run would otherwise grow the
in-memory state without bound — eventually OOMing the runner or freezing
the live tree renderer.

Enforcement rules:

- ``MAX_PLAYS`` (1000): when ``len(state.plays)`` is already at the cap, the
  next ``v2_playbook_on_play_start`` is dropped and ``truncated_events["plays"]``
  is incremented.
- ``MAX_TASKS_PER_PLAY`` (10000): same pattern, applied per-play to
  ``play.tasks``. Counter ``"tasks"``.
- ``MAX_HOSTS_PER_TASK`` (10000): same pattern, applied per-task to
  ``task.hosts``. Counter ``"hosts"``.
- ``MAX_TOTAL_HOST_RUN_STATES`` (1 000 000): a single global counter; the
  1 000 001st ``HostRunState`` insertion (across the entire run) is
  dropped and ``truncated_events["total_hosts"]`` is incremented.

The truncated counts surface through ``state.truncated_events`` and the
``compact`` / ``tui`` renderers append a one-line footer so users can
see something was clipped.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ansible_aom.core.run_state import RunState
from ansible_aom.core.state_machine import (
    MAX_HOSTS_PER_TASK,
    MAX_PLAYS,
    MAX_TASKS_PER_PLAY,
    MAX_TOTAL_HOST_RUN_STATES,
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _play_start(play_id: str, name: str) -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": _ts(),
        "play": {"id": play_id, "name": name},
    }


def _task_start(task_id: str, task_name: str, play_id: str) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": _ts(),
        "task": {"id": task_id, "name": task_name},
        "play": {"id": play_id},
    }


def _runner_on_ok(task_id: str, play_id: str, hostname: str, **kwargs: object) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": _ts(),
        "task": {"id": task_id},
        "play": {"id": play_id},
        "hosts": {hostname: {"changed": kwargs.get("changed", False)}},
    }


def test_max_plays_enforced() -> None:
    """R12: the 1001st ``v2_playbook_on_play_start`` is dropped."""
    state = RunState(playbook="x")
    # Feed MAX_PLAYS plays — all accepted.
    for i in range(MAX_PLAYS):
        state.handle_event(_play_start(f"play-{i}", f"Play {i}"))
    assert len(state.plays) == MAX_PLAYS
    # The next one is dropped.
    state.handle_event(_play_start(f"play-{MAX_PLAYS}", f"Play {MAX_PLAYS}"))
    assert len(state.plays) == MAX_PLAYS
    assert state.truncated_events["plays"] == 1
    # Subsequent ones keep incrementing the counter.
    state.handle_event(_play_start(f"play-{MAX_PLAYS + 1}", f"Play {MAX_PLAYS + 1}"))
    assert state.truncated_events["plays"] == 2


def test_max_tasks_per_play_enforced() -> None:
    """R12: a play's 10001st task is dropped (other plays unaffected)."""
    state = RunState(playbook="x")
    state.handle_event(_play_start("p1", "Play 1"))
    for i in range(MAX_TASKS_PER_PLAY):
        state.handle_event(_task_start(f"t-{i}", f"Task {i}", "p1"))
    assert len(state.plays["p1"].tasks) == MAX_TASKS_PER_PLAY
    # 10001st task dropped.
    state.handle_event(_task_start("t-extra", "Extra", "p1"))
    assert len(state.plays["p1"].tasks) == MAX_TASKS_PER_PLAY
    assert state.truncated_events["tasks"] == 1
    # And another play isn't blocked by the first play's cap.
    state.handle_event(_play_start("p2", "Play 2"))
    state.handle_event(_task_start("t2-0", "Task 0 in p2", "p2"))
    assert "p2" in state.plays
    assert len(state.plays["p2"].tasks) == 1


def test_max_hosts_per_task_enforced() -> None:
    """R12: a task's 10001st host is dropped."""
    state = RunState(playbook="x")
    state.handle_event(_play_start("p1", "Play 1"))
    state.handle_event(_task_start("t1", "Task 1", "p1"))
    # Feed MAX_HOSTS_PER_TASK events. v2_runner_on_ok mutates
    # task.hosts[hostname] (replaces), so use v2_runner_on_start to add
    # hosts to MAX and then expect the next one is dropped.
    for i in range(MAX_HOSTS_PER_TASK):
        state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": _ts(),
                "host": f"h-{i}",
                "task": {"id": "t1"},
                "play": {"id": "p1"},
            }
        )
    assert len(state.plays["p1"].tasks["t1"].hosts) == MAX_HOSTS_PER_TASK
    # 10001st host dropped.
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": _ts(),
            "host": "h-extra",
            "task": {"id": "t1"},
            "play": {"id": "p1"},
        }
    )
    assert len(state.plays["p1"].tasks["t1"].hosts) == MAX_HOSTS_PER_TASK
    assert state.truncated_events["hosts"] == 1


def test_max_total_host_run_states_enforced() -> None:
    """R12: the 1 000 001st HostRunState insertion is dropped.

    The MAX_TOTAL_HOST_RUN_STATES cap is shared across the entire run.
    Feeding that many real events through the state machine would
    allocate a million ``HostRunState`` objects — too slow for a unit
    test. Instead we pre-fill ``state._total_host_run_states`` directly
    to ``MAX_TOTAL_HOST_RUN_STATES - 1`` (one slot remaining) and feed
    two more events: the next insertion should still succeed, the
    one after that must be dropped and increment the counter.
    """
    state = RunState(playbook="x")
    state.handle_event(_play_start("p1", "Play 1"))
    state.handle_event(_task_start("t1", "Task 1", "p1"))
    # One slot away from the cap.
    state._total_host_run_states = MAX_TOTAL_HOST_RUN_STATES - 1

    # This insertion lands in the last remaining slot.
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": _ts(),
            "host": "h-0",
            "task": {"id": "t1"},
            "play": {"id": "p1"},
        }
    )
    assert state._total_host_run_states == MAX_TOTAL_HOST_RUN_STATES
    assert state.truncated_events.get("total_hosts", 0) == 0

    # The next insertion must be dropped.
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": _ts(),
            "host": "h-1",
            "task": {"id": "t1"},
            "play": {"id": "p1"},
        }
    )
    assert state.truncated_events["total_hosts"] == 1


def test_truncated_events_starts_empty() -> None:
    """R12: a fresh RunState has no truncations recorded."""
    state = RunState(playbook="x")
    assert state.truncated_events == {}


def test_truncated_events_independent_counters() -> None:
    """R12: each cap has its own counter, not shared."""
    state = RunState(playbook="x")
    # Fill plays and tasks — both should record distinct counters.
    for i in range(MAX_PLAYS):
        state.handle_event(_play_start(f"p-{i}", f"Play {i}"))
    # Pre-fill p-0 to MAX_TASKS_PER_PLAY - 1 (one slot remaining), then
    # add two more tasks — the first lands in the last slot, the second
    # is the first truncated "tasks" event.
    for i in range(MAX_TASKS_PER_PLAY - 1):
        state.handle_event(_task_start(f"t-{i}", f"Task {i}", "p-0"))
    state.handle_event(_task_start("t-x", "Fills last slot", "p-0"))
    state.handle_event(_task_start("t-y", "Dropped", "p-0"))
    assert state.truncated_events.get("plays", 0) == 0
    assert state.truncated_events["tasks"] == 1


def test_truncated_constants_pinned() -> None:
    """R12: pin the documented cap values so accidental edits are caught."""
    assert MAX_PLAYS == 1000
    assert MAX_TASKS_PER_PLAY == 10_000
    assert MAX_HOSTS_PER_TASK == 10_000
    assert MAX_TOTAL_HOST_RUN_STATES == 1_000_000
