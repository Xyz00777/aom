"""Regression tests for hostless meta-task projection."""

from __future__ import annotations

# pyright: reportMissingImports=false
from ansible_aom.core.models import PlayDefinition, Status, TaskDefinition
from ansible_aom.core.run_state import RunState
from ansible_aom.core.tree import TreeProjection


def _hostless_task_state(task_name: str) -> RunState:
    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="p1",
            name="deploy",
            hosts="webservers",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name=task_name,
                    role=None,
                    tags=[],
                    play_id="p1",
                    play_order=0,
                    task_order=0,
                )
            ],
        )
    ]
    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-1", "name": "deploy"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": task_name},
            "play": {"id": "play-1"},
        }
    )
    return state


def test_meta_task_does_not_synthesize_fake_host_leaves() -> None:
    state = _hostless_task_state("meta: flush_handlers")
    lines = TreeProjection.from_run_state(state).tree_lines(budget=20)

    assert any(ln.kind == "task" and ln.status == Status.RUNNING for ln in lines)
    assert any(ln.kind == "task" and ln.label.startswith("meta: flush_handlers") for ln in lines)
    assert not any(ln.kind == "host" for ln in lines)


def test_normal_hostless_task_still_synthesizes_host_leaves() -> None:
    state = _hostless_task_state("Install nginx")
    lines = TreeProjection.from_run_state(state).tree_lines(budget=20)

    host_lines = [ln for ln in lines if ln.kind == "host"]
    assert [ln.label for ln in host_lines] == ["web1"]
    assert all(hl.status == Status.RUNNING for hl in host_lines)


def test_meta_task_gap_keeps_earlier_completed_plays_hidden() -> None:
    from datetime import datetime, timedelta, timezone

    state = RunState(playbook="site.yml")
    state.definitions = [
        PlayDefinition(
            id="p1",
            name="Play One",
            hosts="webservers",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="Cleanup old state",
                    role=None,
                    tags=[],
                    play_id="p1",
                    play_order=0,
                    task_order=0,
                )
            ],
        ),
        PlayDefinition(
            id="p2",
            name="Play Two",
            hosts="webservers",
            resolved_hosts=["web1"],
            tasks=[
                TaskDefinition(
                    name="meta: flush_handlers",
                    role=None,
                    tags=[],
                    play_id="p2",
                    play_order=1,
                    task_order=0,
                ),
                TaskDefinition(
                    name="Install nginx",
                    role=None,
                    tags=[],
                    play_id="p2",
                    play_order=1,
                    task_order=1,
                ),
            ],
        ),
    ]

    state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-1", "name": "Play One"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Cleanup old state"},
            "play": {"id": "play-1"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Cleanup old state"},
            "host": "web1",
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "t1", "name": "Cleanup old state"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:06Z",
            "play": {"id": "play-2", "name": "Play Two"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:07Z",
            "task": {"id": "t-meta", "name": "meta: flush_handlers"},
            "play": {"id": "play-2"},
        }
    )

    projection = TreeProjection.from_run_state(state)
    frame_now = datetime(2026, 4, 20, 10, 0, 8, tzinfo=timezone.utc)

    lines1 = projection.tree_lines(budget=20, now=frame_now)
    assert any(ln.kind == "task" and ln.label.startswith("meta: flush_handlers") for ln in lines1)
    assert not any(ln.kind == "host" for ln in lines1)
    assert not any(ln.kind == "play" and ln.label == "play: Play One" for ln in lines1)

    state.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:09Z",
            "task": {"id": "t2", "name": "Install nginx"},
            "play": {"id": "play-2"},
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:10Z",
            "task": {"id": "t2", "name": "Install nginx"},
            "host": "web1",
        }
    )
    state.handle_event(
        {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:12Z",
            "task": {"id": "t2", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True, "changed": False}},
        }
    )

    lines2 = projection.tree_lines(budget=20, now=frame_now + timedelta(seconds=5))
    assert not any(ln.kind == "play" and ln.label == "play: Play Two" for ln in lines2)
    assert not any(ln.kind == "play" and ln.label == "play: Play One" for ln in lines2)
