from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition

TASK_NAME = "example : Dynamic task"
TASK_PATH = "roles/example/tasks/main.yml:7"


def _renderer(hosts: list[str]) -> CompactRenderer:
    renderer = CompactRenderer(is_tty=False)
    renderer.start("test.yml", [])
    renderer._colorize = False
    renderer._display = MagicMock()
    renderer.set_definitions(
        [PlayDefinition(id="p1", name="P", hosts="all", resolved_hosts=hosts, tasks=[])]
    )
    renderer.update_state(
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "P"}}
    )
    return renderer


def _start(task_id: str, host: str, *, name: str = TASK_NAME, path: str = TASK_PATH) -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-05-11T10:00:00Z",
        "task": {"id": task_id, "name": name, "path": path},
        "host": host,
    }


def _ok(task_id: str, host: str, *, name: str = TASK_NAME, path: str = TASK_PATH) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": task_id, "name": name, "path": path},
        "hosts": {host: {"changed": False}},
    }


def _summary_lines(renderer: CompactRenderer, name: str = TASK_NAME) -> list[str]:
    return [
        call.args[0]
        for call in renderer._display.print_log.call_args_list
        if name in call.args[0] and " — " in call.args[0]
    ]


def test_fanout_per_host_uuids_summarise_when_their_hosts_finish() -> None:
    renderer = _renderer(["a", "b"])
    renderer.update_state(_start("u1", "a"))
    renderer.update_state(_start("u2", "b"))
    renderer.update_state(_ok("u2", "b"))

    renderer.update_state(_ok("u1", "a"))

    # The last ok completes the group → BOTH members summarise immediately.
    assert len(_summary_lines(renderer)) == 2
    renderer.handle_completion(130, "crashed")
    assert len(_summary_lines(renderer)) == 2


def test_fanout_peer_running_blocks_summary() -> None:
    renderer = _renderer(["a", "b"])
    renderer.update_state(_start("u1", "a"))
    renderer.update_state(_start("u2", "b"))

    renderer.update_state(_ok("u1", "a"))

    assert not _summary_lines(renderer)


def test_fanout_last_ok_flushes_all_members() -> None:
    """A 3-member group: the final ok must summarise every member
    immediately — no member may linger until the run-end force flush."""
    renderer = _renderer(["a", "b", "c"])
    renderer.update_state(_start("u1", "a"))
    renderer.update_state(_start("u2", "b"))
    renderer.update_state(_start("u3", "c"))
    renderer.update_state(_ok("u3", "c"))
    renderer.update_state(_ok("u2", "b"))
    assert not _summary_lines(renderer)  # u1 still running
    renderer.update_state(_ok("u1", "a"))
    assert len(_summary_lines(renderer)) == 3
    renderer.handle_completion(130, "crashed")
    assert len(_summary_lines(renderer)) == 3


def test_fanout_no_flood_at_cancel() -> None:
    renderer = _renderer(["a", "b"])
    renderer.update_state(_start("u1", "a"))
    renderer.update_state(_start("u2", "b"))
    renderer.update_state(_ok("u2", "b"))
    renderer.update_state(_ok("u1", "a"))
    renderer.update_state(_start("next", "a", name="Next", path="site.yml:20"))
    summaries_before_cancel = len(_summary_lines(renderer))
    assert ("p1", TASK_NAME, TASK_PATH) not in renderer._fan_out_groups

    renderer.handle_completion(130, "crashed")

    assert summaries_before_cancel == 2
    assert len(_summary_lines(renderer)) == summaries_before_cancel


def test_shared_uuid_still_waits_for_all_targets() -> None:
    renderer = _renderer(["a", "b"])
    renderer.update_state(_start("u1", "a"))
    renderer.update_state(_ok("u1", "a"))

    renderer.update_state(_start("next", "a", name="Next", path="site.yml:20"))

    assert not _summary_lines(renderer)
    renderer.handle_completion(130, "crashed")
    assert len(_summary_lines(renderer)) == 1
