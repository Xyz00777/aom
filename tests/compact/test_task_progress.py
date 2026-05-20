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


def test_count_completed_tasks_counts_tasks_with_host_results():
    """A task counts as complete once any host has reported a result.

    Mirrors the real flow: ``_handle_v2_runner_on_ok`` populates
    ``task.hosts``; tasks announced but not yet executed have empty hosts.
    """
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web")

    done_ok = TaskRunState(task_id="t1", name="done-ok")
    done_ok.hosts["w1"] = HostRunState(hostname="w1", status=Status.OK)

    done_failed = TaskRunState(task_id="t2", name="done-failed")
    done_failed.hosts["w1"] = HostRunState(hostname="w1", status=Status.FAILED)

    # Announced but no host events yet — in flight, should NOT count.
    running = TaskRunState(task_id="t3", name="running", status=Status.RUNNING)
    pending = TaskRunState(task_id="t4", name="pending", status=Status.PENDING)

    play.tasks["t1"] = done_ok
    play.tasks["t2"] = done_failed
    play.tasks["t3"] = running
    play.tasks["t4"] = pending
    state.plays["1"] = play

    assert count_completed_tasks(state) == 2


def test_count_completed_tasks_counts_skipped_and_unreachable_results():
    """Skipped / unreachable / changed host results all count as task completion."""
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web")

    skipped = TaskRunState(task_id="t1", name="skipped")
    skipped.hosts["w1"] = HostRunState(hostname="w1", status=Status.SKIPPED)

    unreachable = TaskRunState(task_id="t2", name="unreachable")
    unreachable.hosts["w1"] = HostRunState(hostname="w1", status=Status.UNREACHABLE)

    changed = TaskRunState(task_id="t3", name="changed")
    changed.hosts["w1"] = HostRunState(hostname="w1", status=Status.CHANGED)

    play.tasks["t1"] = skipped
    play.tasks["t2"] = unreachable
    play.tasks["t3"] = changed
    state.plays["1"] = play

    assert count_completed_tasks(state) == 3


def test_count_completed_tasks_empty_state():
    assert count_completed_tasks(RunState(playbook="site.yml")) == 0


def test_count_total_tasks_grows_with_runtime_announced_tasks():
    """Preflight `--list-tasks` only sees static + import_tasks. Dynamic
    `include_tasks` expand at runtime — runtime task count exceeds the
    preflight count. The denominator shown in the status bar should
    take `max(preflight_total, runtime_announced)` so the ratio never
    shows `N/M` with N > M. Regression guard for: '30/4 tasks' user
    report where runtime had 30 announced tasks but preflight saw 4."""
    from ansible_aom.compact.renderer import count_total_tasks_seen

    # Preflight saw 4 leaf tasks.
    preflight = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=["h1"],
            tasks=[_task(f"static-{i}", "1", i) for i in range(4)],
        ),
    ]
    # Runtime has announced 30 tasks (via dynamic include_tasks).
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="deploy")
    for i in range(30):
        play.tasks[f"runtime-{i}"] = TaskRunState(
            task_id=f"runtime-{i}",
            name=f"task-{i}",
        )
    state.plays["1"] = play
    # Result: max(4, 30) == 30 — the running upper bound.
    assert count_total_tasks_seen(preflight, state) == 30


def test_handle_completion_keeps_runtime_grown_denominator():
    """When the run cancels mid-flight the final status bar must NOT
    revert to the preflight-only task total — it must keep using the
    runtime-grown denominator (max of preflight and announced).
    Regression guard for: user reported `30/4 tasks` after Ctrl+C even
    though during execution the count was correct."""
    from unittest.mock import patch

    from ansible_aom.compact.renderer import CompactRenderer

    r = CompactRenderer(is_tty=False)
    r.start("site.yml", [])
    # Preflight said 4 tasks; runtime announced 30 (dynamic includes).
    r._definitions = [
        PlayDefinition(
            id="1",
            name="big",
            hosts="all",
            resolved_hosts=["h1"],
            tasks=[_task(f"static-{i}", "1", i) for i in range(4)],
        ),
    ]
    assert r._state is not None
    r._state.definitions = list(r._definitions)
    play = PlayRunState(play_id="1", name="big")
    for i in range(30):
        play.tasks[f"runtime-{i}"] = TaskRunState(
            task_id=f"runtime-{i}",
            name=f"t{i}",
        )
        play.tasks[f"runtime-{i}"].hosts["h1"] = HostRunState(
            hostname="h1",
            status=Status.OK,
        )
    r._state.plays["1"] = play

    with patch.object(r._display, "update") as m:
        r.handle_completion(130, "crashed")
    args, kwargs = m.call_args
    content = args[0] if args else kwargs.get("content")
    assert content is not None
    # Denominator must be the runtime grown count (30), not preflight (4).
    assert "30/30 tasks" in content or "30 / 30 tasks" in content, (
        f"expected '30/30 tasks' in final status, got: {content!r}"
    )


def test_count_total_tasks_seen_falls_back_to_preflight_before_any_announce():
    """At the start of a run, before any task_start event, the runtime
    count is 0. The denominator should be the preflight count, not 0."""
    from ansible_aom.compact.renderer import count_total_tasks_seen

    preflight = [
        PlayDefinition(
            id="1",
            name="deploy",
            hosts="all",
            resolved_hosts=["h1"],
            tasks=[_task("a", "1", 0), _task("b", "1", 1)],
        ),
    ]
    state = RunState(playbook="site.yml")
    assert count_total_tasks_seen(preflight, state) == 2


def test_count_completed_tasks_excludes_tasks_with_running_hosts():
    """A task whose hosts dict contains a RUNNING entry is in-flight,
    not completed. The state machine's `_handle_v2_runner_on_start`
    populates `task.hosts` with HostRunState(RUNNING) on host start, so
    'non-empty hosts' alone is no longer sufficient to mean 'completed'
    — we must also require no host be in RUNNING state. Regression
    guard for a bug where every announced task was counted as
    completed, producing nonsense ratios like `30/4 tasks`."""
    state = RunState(playbook="site.yml")
    play = PlayRunState(play_id="1", name="web")

    in_flight = TaskRunState(task_id="t1", name="in-flight", status=Status.RUNNING)
    in_flight.hosts["w1"] = HostRunState(hostname="w1", status=Status.RUNNING)

    done = TaskRunState(task_id="t2", name="done")
    done.hosts["w1"] = HostRunState(hostname="w1", status=Status.OK)

    partially_done = TaskRunState(task_id="t3", name="partially-done")
    partially_done.hosts["w1"] = HostRunState(hostname="w1", status=Status.OK)
    partially_done.hosts["w2"] = HostRunState(hostname="w2", status=Status.RUNNING)

    play.tasks["t1"] = in_flight
    play.tasks["t2"] = done
    play.tasks["t3"] = partially_done
    state.plays["1"] = play

    # Only t2 (all hosts terminal) counts as completed.
    assert count_completed_tasks(state) == 1


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
