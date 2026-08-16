"""Tests for ``task_complete_on_all_targets`` — the full-play-completion
predicate that drives the compact renderer's per-task summary timing.

A task is complete only when every *live target* host (the play's
preflight-resolved host set minus hosts that went FAILED/UNREACHABLE)
has a terminal (non-RUNNING) result for the task. This is deliberately
NOT "all started hosts terminal": under a free/host-pinned strategy a
host can start a task long after its peers finished it, so the started
set is not the target set.
"""

from __future__ import annotations

from ansible_aom.core.models import PlayDefinition, RunState
from ansible_aom.core.tree_projection import task_complete_on_all_targets


def _play_def(play_id: str, hosts: list[str]) -> PlayDefinition:
    return PlayDefinition(id=play_id, name="P", hosts="all", resolved_hosts=list(hosts), tasks=[])


def _play_start(play_id: str = "p1") -> dict:
    return {"_event": "v2_playbook_on_play_start", "play": {"id": play_id, "name": "P"}}


def _runner_start(
    task_id: str,
    host: str,
    play_id: str = "p1",
    *,
    task_name: str = "T",
    task_path: str | None = None,
) -> dict:
    task = {"id": task_id, "name": task_name}
    if task_path is not None:
        task["path"] = task_path
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-05-11T10:00:00Z",
        "task": task,
        "play": {"id": play_id},
        "host": host,
    }


def _ok(task_id: str, host: str, play_id: str = "p1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": task_id, "name": "T"},
        "play": {"id": play_id},
        "hosts": {host: {"changed": False}},
    }


def _failed(task_id: str, host: str, play_id: str = "p1") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": task_id, "name": "T"},
        "play": {"id": play_id},
        "hosts": {host: {"failed": True, "msg": "boom"}},
    }


def _state(hosts: list[str]) -> RunState:
    s = RunState(playbook="site.yml")
    # Assigning ``definitions`` rebuilds the play-def indexes via __setattr__.
    s.definitions = [_play_def("p1", hosts)]
    s.handle_event(_play_start())
    return s


def _ran_ok(s: RunState, task_id: str, host: str) -> None:
    """Fire the real free-strategy pair: start then ok."""
    s.handle_event(_runner_start(task_id, host))
    s.handle_event(_ok(task_id, host))


def test_incomplete_while_a_target_host_has_not_finished() -> None:
    """3 targets, only 2 finished → not complete (the 3rd hasn't run it)."""
    s = _state(["a", "b", "c"])
    _ran_ok(s, "t1", "a")
    _ran_ok(s, "t1", "b")
    assert task_complete_on_all_targets(s, "t1") is False


def test_complete_when_all_targets_terminal() -> None:
    s = _state(["a", "b", "c"])
    _ran_ok(s, "t1", "a")
    _ran_ok(s, "t1", "b")
    _ran_ok(s, "t1", "c")
    assert task_complete_on_all_targets(s, "t1") is True


def test_running_host_blocks_completion() -> None:
    """A host mid-run (started, not terminal) blocks completion."""
    s = _state(["a", "b"])
    _ran_ok(s, "t1", "a")
    s.handle_event(_runner_start("t1", "b"))  # b started, no terminal yet
    assert task_complete_on_all_targets(s, "t1") is False


def test_dead_host_does_not_block_later_task() -> None:
    """A host that failed earlier is dropped from the play and must not
    block completion of a later task it never reaches."""
    s = _state(["a", "b"])
    # b fails task t1 → removed from play for subsequent tasks.
    _ran_ok(s, "t1", "a")
    s.handle_event(_runner_start("t1", "b"))
    s.handle_event(_failed("t1", "b"))
    # t2 runs only on the survivor a.
    _ran_ok(s, "t2", "a")
    assert task_complete_on_all_targets(s, "t2") is True


def test_early_task_not_complete_before_slow_targets_start() -> None:
    """The undercount guard: with a fork limit, a fast cohort finishes
    the task while other targets haven't started it. Must NOT be complete."""
    s = _state(["a", "b", "c", "d", "e"])
    _ran_ok(s, "t1", "a")
    _ran_ok(s, "t1", "b")  # c, d, e have not started t1 yet
    assert task_complete_on_all_targets(s, "t1") is False


def test_all_hosts_failed_in_task_is_complete() -> None:
    """A host that died *in* this task finished it (by failing) and is
    counted — an all-failed task is complete, not stuck pending."""
    s = _state(["a", "b"])
    s.handle_event(_runner_start("t1", "a"))
    s.handle_event(_failed("t1", "a"))
    s.handle_event(_runner_start("t1", "b"))
    s.handle_event(_failed("t1", "b"))
    assert task_complete_on_all_targets(s, "t1") is True


def test_unknown_task_is_not_complete() -> None:
    s = _state(["a"])
    assert task_complete_on_all_targets(s, "does-not-exist") is False


def test_no_target_information_is_not_complete() -> None:
    """No preflight hosts and no runtime hosts → cannot assert completion."""
    s = RunState(playbook="site.yml")
    s.handle_event(_play_start())
    assert task_complete_on_all_targets(s, "t1") is False


def test_fan_out_member_complete_when_group_hosts_terminal() -> None:
    s = _state(["a", "b", "c"])
    path = "roles/example/tasks/main.yml:7"
    _ran_ok_with_meta(s, "u1", "a", path)
    _ran_ok_with_meta(s, "u2", "b", path)
    groups = {("p1", "T", path): {"u1", "u2"}}

    assert task_complete_on_all_targets(s, "u1", fan_out_groups=groups) is True
    assert task_complete_on_all_targets(s, "u2", fan_out_groups=groups) is True
    assert task_complete_on_all_targets(s, "u1") is False
    assert task_complete_on_all_targets(s, "u2") is False


def test_fan_out_group_blocks_until_all_members_terminal() -> None:
    s = _state(["a", "b"])
    path = "roles/example/tasks/main.yml:7"
    _ran_ok_with_meta(s, "u1", "a", path)
    s.handle_event(_runner_start("u2", "b", task_path=path))
    groups = {("p1", "T", path): {"u1", "u2"}}

    assert task_complete_on_all_targets(s, "u1", fan_out_groups=groups) is False


def test_fan_out_ignores_dead_hosts() -> None:
    s = _state(["a", "b"])
    path = "roles/example/tasks/main.yml:7"
    _ran_ok_with_meta(s, "u1", "a", path)
    s.handle_event(_runner_start("u2", "b", task_path=path))
    s.handle_event(_runner_start("killer", "b"))
    s.handle_event(_failed("killer", "b"))
    groups = {("p1", "T", path): {"u1", "u2"}}

    assert task_complete_on_all_targets(s, "u1", fan_out_groups=groups) is True


def test_single_instance_keeps_old_semantics() -> None:
    s = _state(["a", "b"])
    path = "roles/example/tasks/main.yml:7"
    _ran_ok_with_meta(s, "u1", "a", path)
    groups = {("p1", "T", path): {"u1"}}

    assert task_complete_on_all_targets(s, "u1", fan_out_groups=groups) is False


def _ran_ok_with_meta(s: RunState, task_id: str, host: str, path: str) -> None:
    s.handle_event(_runner_start(task_id, host, task_path=path))
    s.handle_event(_ok(task_id, host))
