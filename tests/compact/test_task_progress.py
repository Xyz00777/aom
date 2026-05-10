"""Tests for task-progress display in the compact status bar.

The status bar already shows hosts completed (`3/10 hosts`); for
playbooks where the static task list is known up-front (the common
case — only `include_tasks` defers expansion), it should also show
how far we are through the work: `5/47 tasks`. Without this, on a
50-task playbook the user can't tell whether they're 10% or 90%
through the run.

Total comes from preflight definitions; completed comes from RunState
task entries that have moved past PENDING/RUNNING.
"""

from __future__ import annotations

from ansible_aom.compact.renderer import (
    count_completed_tasks,
    count_total_tasks,
    format_status_bar,
)
from ansible_aom.core.models import (
    HostRunState,
    PlayDefinition,
    PlayRunState,
    RunState,
    Status,
    TaskDefinition,
    TaskRunState,
)


def test_format_status_bar_includes_task_progress_when_total_set():
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=2,
        hosts_total=5,
        warnings=0,
        deprecations=0,
        elapsed_seconds=10,
        tasks_completed=3,
        tasks_total=12,
    )
    assert "3/12 tasks" in result


def test_format_status_bar_omits_tasks_when_total_zero():
    """If preflight didn't yield a task count, suppress the segment entirely."""
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=0,
        hosts_total=5,
        warnings=0,
        deprecations=0,
        elapsed_seconds=0,
        tasks_completed=0,
        tasks_total=0,
    )
    assert "tasks" not in result


def test_format_status_bar_task_progress_defaults_to_zero():
    """Existing callers that pre-date this feature still produce a clean bar."""
    result = format_status_bar(
        playbook="site.yml",
        hosts_completed=1,
        hosts_total=5,
        warnings=0,
        deprecations=0,
        elapsed_seconds=10,
    )
    assert "tasks" not in result


def _task(name: str, play_id: str, order: int) -> TaskDefinition:
    return TaskDefinition(
        name=name, role=None, tags=[], play_id=play_id, play_order=0, task_order=order
    )


def test_count_total_tasks_sums_across_plays():
    play_a = PlayDefinition(
        id="1",
        name="web",
        hosts="webservers",
        tasks=[_task("t1", "1", 0), _task("t2", "1", 1)],
    )
    play_b = PlayDefinition(
        id="2",
        name="db",
        hosts="dbservers",
        tasks=[_task("t3", "2", 0)],
    )
    assert count_total_tasks([play_a, play_b]) == 3


def test_count_total_tasks_empty():
    assert count_total_tasks([]) == 0


def test_count_completed_tasks_counts_only_terminal_tasks():
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web")

    done_ok = TaskRunState(task_id="t1", name="done-ok", status=Status.OK)
    done_ok.hosts["w1"] = HostRunState(hostname="w1", status=Status.OK)

    done_failed = TaskRunState(task_id="t2", name="done-failed", status=Status.FAILED)
    done_failed.hosts["w1"] = HostRunState(hostname="w1", status=Status.FAILED)

    running = TaskRunState(task_id="t3", name="running", status=Status.RUNNING)
    pending = TaskRunState(task_id="t4", name="pending", status=Status.PENDING)

    play.tasks["t1"] = done_ok
    play.tasks["t2"] = done_failed
    play.tasks["t3"] = running
    play.tasks["t4"] = pending
    state.plays["1"] = play

    assert count_completed_tasks(state) == 2


def test_count_completed_tasks_treats_skipped_and_unreachable_as_done():
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web")

    skipped = TaskRunState(task_id="t1", name="skipped", status=Status.SKIPPED)
    unreachable = TaskRunState(task_id="t2", name="unreachable", status=Status.UNREACHABLE)
    completed = TaskRunState(task_id="t3", name="completed", status=Status.COMPLETED)
    changed = TaskRunState(task_id="t4", name="changed", status=Status.CHANGED)

    play.tasks["t1"] = skipped
    play.tasks["t2"] = unreachable
    play.tasks["t3"] = completed
    play.tasks["t4"] = changed
    state.plays["1"] = play

    assert count_completed_tasks(state) == 4


def test_count_completed_tasks_empty_state():
    assert count_completed_tasks(RunState(playbook="site.yml")) == 0


def test_renderer_status_bar_reflects_task_progress(monkeypatch):
    """Wire-up: renderer.tick() should refresh status bar with current task progress."""
    from ansible_aom.compact.renderer import CompactRenderer

    captured: list[str] = []

    class FakeDisplay:
        def start(self):
            pass

        def stop(self):
            pass

        def update(self, text: str) -> None:
            captured.append(text)

        def print_log(self, message: str) -> None:
            pass

    renderer = CompactRenderer(is_tty=True)
    monkeypatch.setattr(renderer, "_display", FakeDisplay())

    renderer.start("site.yml", [])

    play_def = PlayDefinition(
        id="1",
        name="web",
        hosts="webservers",
        resolved_hosts=["w1"],
        tasks=[_task("a", "1", 0), _task("b", "1", 1), _task("c", "1", 2)],
    )
    renderer.set_definitions([play_def])

    assert renderer._state is not None
    play = PlayRunState(play_id="1", name="web", status=Status.RUNNING)
    done = TaskRunState(task_id="t1", name="a", status=Status.OK)
    done.hosts["w1"] = HostRunState(hostname="w1", status=Status.OK)
    play.tasks["t1"] = done
    renderer._state.plays["1"] = play

    renderer.tick()

    assert any("1/3 tasks" in frame for frame in captured), captured
