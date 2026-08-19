"""Tests ensuring tasks_total is never less than tasks_completed in summary calculation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from ansible_aom.compact.format import count_total_tasks_seen, format_status_bar
from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import (
    PlayDefinition,
    PlayRunState,
    RunState,
    TaskRunState,
)
from ansible_aom.session.history import PriorRun, _mine_task_wall


def test_format_status_bar_clamps_tasks_total_to_tasks_completed() -> None:
    """format_status_bar must never show tasks_completed > tasks_total."""
    result = format_status_bar(
        playbook="main.yml",
        hosts_completed=19,
        hosts_total=19,
        warnings=6,
        deprecations=3,
        elapsed_seconds=13798,
        tasks_completed=4956,
        tasks_total=4156,
    )
    assert "4956/4956 tasks" in result
    assert "4956/4156 tasks" not in result


def test_format_status_bar_estimated_drops_tilde_when_overtaken() -> None:
    """When completed tasks reach or exceed estimated total, the estimate tilde is dropped."""
    result = format_status_bar(
        playbook="main.yml",
        hosts_completed=19,
        hosts_total=19,
        warnings=0,
        deprecations=0,
        elapsed_seconds=100,
        tasks_completed=4956,
        tasks_total=4156,
        estimated_total=True,
    )
    assert "4956/4956 tasks" in result
    assert "~" not in result


def test_renderer_status_panel_tasks_total_with_smaller_prior() -> None:
    """When live completed tasks exceed prior run's observed_task_count,
    tasks_total reflects actual.
    """
    r = CompactRenderer(is_tty=False)
    r.start("main.yml", [])
    r._colorize = False
    r._display = MagicMock()

    prior = PriorRun(
        session_id="s1",
        duration_seconds=1000.0,
        task_count=100,
        host_count=19,
        end_time=datetime.now(timezone.utc),
        observed_task_count=4156,
        exact_match=False,
    )
    r.set_prior_run(prior)

    # Simulate completed tasks reaching 4956
    r._tasks_completed = 4956
    r._tasks_seen = 4156

    total, estimated = r._task_total_with_prior(4156)
    assert total >= 4956
    assert not estimated


def test_renderer_tasks_seen_updated_on_runner_on_start_and_terminal() -> None:
    """Under free strategy and dynamic tasks, _tasks_seen tracks all seen tasks."""
    r = CompactRenderer(is_tty=False)
    r.start("main.yml", [])
    r._colorize = False
    r._display = MagicMock()

    # Free strategy runner on start
    r.update_state(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-08-19T20:00:00Z",
            "play": {"id": "p1"},
            "task": {"id": "t1", "name": "Free task 1"},
            "host": "h1",
        }
    )
    assert r._tasks_seen >= 1


def test_count_total_tasks_seen_always_at_least_completed() -> None:
    """count_total_tasks_seen must never return less than count_completed_tasks."""
    state = RunState(playbook="main.yml")
    play = PlayRunState(play_id="p1", name="play1")
    for i in range(5):
        t = TaskRunState(task_id=f"t{i}", name=f"task {i}")
        play.tasks[f"t{i}"] = t
    state.plays["p1"] = play

    defs: list[PlayDefinition] = []
    assert count_total_tasks_seen(defs, state) >= 5


def test_mine_task_wall_counts_runner_starts(tmp_path: Path) -> None:
    """_mine_task_wall counts unique tasks even if only runner events are emitted."""
    session_dir = tmp_path / "sess"
    session_dir.mkdir()
    events_file = session_dir / "events.jsonl"
    events = [
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-08-19T20:00:00Z",
            "play": {"id": "p1"},
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-08-19T20:00:01Z",
            "task": {"id": "t1", "path": "roles/a.yml:1"},
            "host": "h1",
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-08-19T20:00:01Z",
            "task": {"id": "t1", "path": "roles/a.yml:1"},
            "host": "h2",
        },
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-08-19T20:00:02Z",
            "task": {"id": "t2", "path": "roles/b.yml:1"},
            "host": "h1",
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-08-19T20:00:03Z",
            "task": {"id": "t1", "path": "roles/a.yml:1"},
            "hosts": {"h1": {}, "h2": {}},
        },
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-08-19T20:00:04Z",
            "task": {"id": "t2", "path": "roles/b.yml:1"},
            "hosts": {"h1": {}},
        },
        {"_event": "v2_playbook_on_stats", "_timestamp": "2026-08-19T20:00:05Z"},
    ]
    with open(events_file, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    *_, observed_task_count = _mine_task_wall(session_dir)
    assert observed_task_count == 2
