"""Regression: a pause task that is the last task of its play must not
linger as RUNNING for the rest of the run.

``ansible.builtin.pause`` (and other controller-side actions) emit NO
``v2_runner_on_ok`` — only a ``v2_playbook_on_task_start``. RunState
synthesises a RUNNING host at task-start (from preflight resolved_hosts),
and nothing ever clears it: the next ``v2_playbook_on_task_start`` is in a
*different* play, so the same-play "previous task is done" cleanup never
fires. The host stayed RUNNING in the tree until the final
``v2_playbook_on_stats`` cleanup — i.e. the pause "stayed around" through
every later play.

A new play starting is definitive proof that all prior plays are done
(ansible runs plays sequentially), so ``v2_playbook_on_play_start`` must
finalise prior plays.
"""

from __future__ import annotations

from ansible_aom.core.models import PlayDefinition, RunState, Status
from ansible_aom.core.tree import TreeProjection

_PLAY1 = "play-confirm-uuid"
_PLAY2 = "play-deploy-uuid"
_PAUSE_TASK = "task-pause-uuid"


def _state_with_two_plays() -> RunState:
    state = RunState(playbook="deploy.yml")
    state.definitions = [
        PlayDefinition(
            id="1",
            name="Confirm deployment",
            hosts="localhost",
            resolved_hosts=["localhost"],
            tasks=[],
        ),
        PlayDefinition(
            id="2",
            name="Deploy Kolai",
            hosts="localhost",
            resolved_hosts=["localhost"],
            tasks=[],
        ),
    ]
    return state


def _play_start(pid: str, name: str, ts: str) -> dict:
    return {
        "_event": "v2_playbook_on_play_start",
        "_timestamp": ts,
        "play": {"id": pid, "name": name},
    }


def _task_start(tid: str, name: str, ts: str) -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": tid, "name": name},
    }


class TestPauseLingerCleared:
    def test_pause_host_cleared_when_next_play_starts(self) -> None:
        state = _state_with_two_plays()
        state.handle_event(_play_start(_PLAY1, "Confirm deployment", "2026-06-13T10:00:00Z"))
        state.handle_event(_task_start(_PAUSE_TASK, "Confirm deployment", "2026-06-13T10:00:01Z"))

        # Precondition: the pause host is synthesised RUNNING and has no
        # terminal event (pause emits none).
        pause = state.plays[_PLAY1].tasks[_PAUSE_TASK]
        assert pause.hosts["localhost"].status == Status.RUNNING

        # The next play starts — the pause must be finalised, not left running.
        state.handle_event(_play_start(_PLAY2, "Deploy Kolai", "2026-06-13T10:00:05Z"))

        assert pause.hosts["localhost"].status != Status.RUNNING
        assert pause.status == Status.COMPLETED

    def test_tree_shows_no_running_pause_during_second_play(self) -> None:
        state = _state_with_two_plays()
        state.handle_event(_play_start(_PLAY1, "Confirm deployment", "2026-06-13T10:00:00Z"))
        state.handle_event(_task_start(_PAUSE_TASK, "Confirm deployment", "2026-06-13T10:00:01Z"))
        state.handle_event(_play_start(_PLAY2, "Deploy Kolai", "2026-06-13T10:00:05Z"))
        state.handle_event(_task_start("task-deploy-uuid", "Do the deploy", "2026-06-13T10:00:06Z"))

        # Ground truth: the pause host must be terminal, not RUNNING, while
        # the second play runs (otherwise the task tree renders it as
        # "Confirm deployment (1 running)" for the rest of the run).
        pause = state.plays[_PLAY1].tasks[_PAUSE_TASK]
        assert pause.hosts["localhost"].status != Status.RUNNING
        assert pause.status == Status.COMPLETED

        proj = TreeProjection.from_run_state(state)
        rows = proj.host_rows()
        on_pause = [r for r in rows if r.current_task == "Confirm deployment"]
        assert on_pause == [], (
            f"pause still shown running: {[(r.hostname, r.current_task) for r in rows]}"
        )

    def test_completed_prior_task_status_preserved(self) -> None:
        """Finalising a prior play must not stomp hosts that already have a
        terminal status (only RUNNING ones are forced to OK)."""
        state = _state_with_two_plays()
        state.handle_event(_play_start(_PLAY1, "Confirm deployment", "2026-06-13T10:00:00Z"))
        state.handle_event(_task_start(_PAUSE_TASK, "Confirm deployment", "2026-06-13T10:00:01Z"))
        # A real terminal event arrives (changed) before the next play.
        state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-06-13T10:00:02Z",
                "task": {"id": _PAUSE_TASK, "name": "Confirm deployment"},
                "hosts": {"localhost": {"changed": True}},
            }
        )
        state.handle_event(_play_start(_PLAY2, "Deploy Kolai", "2026-06-13T10:00:05Z"))

        pause = state.plays[_PLAY1].tasks[_PAUSE_TASK]
        assert pause.hosts["localhost"].status == Status.CHANGED
        assert pause.hosts["localhost"].changed is True
