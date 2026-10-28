"""Linear-strategy host synthesis must not resurrect dropped hosts (#21).

Under the default linear strategy ``ansible.posix.jsonl`` emits no
``v2_runner_on_start``, so ``v2_playbook_on_task_start`` synthesises a
RUNNING entry for every preflight ``resolved_hosts`` target. A host whose
latest result in the play is FAILED (not ignored) or UNREACHABLE has been
dropped by Ansible and never runs later tasks. Synthesising it anyway
showed it "running" the next task, and the next-task / stats cleanup then
flipped that phantom execution to a fabricated OK.

Hosts that are legitimately still active keep being synthesised:
survivors, ``ignore_errors`` failures (recorded as OK), and a host whose
failure was followed by a later real result in the play (rescue).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ansible_aom.core.includes import graft_include_children
from ansible_aom.core.models import PlayDefinition, RunState, Status, TaskDefinition
from ansible_aom.core.tree_projection import (
    HostRow,
    TreeProjection,
    _pending_host_count,
    play_dead_hosts,
)


def _state(hosts: list[str]) -> RunState:
    s = RunState(playbook="test.yml")
    s.definitions = [PlayDefinition("1", "Deploy", "all", resolved_hosts=hosts)]
    s.handle_event({"_event": "v2_playbook_on_play_start", "play": {"id": "p", "name": "Deploy"}})
    return s


def _task_start(s: RunState, task_id: str, name: str) -> None:
    s.handle_event({"_event": "v2_playbook_on_task_start", "task": {"id": task_id, "name": name}})


def _result(s: RunState, event: str, task_id: str, host: str, **result: object) -> None:
    s.handle_event({"_event": event, "task": {"id": task_id}, "hosts": {host: result}})


def _rows(s: RunState) -> dict[str, HostRow]:
    return {r.hostname: r for r in TreeProjection.from_run_state(s).host_rows()}


def _run_until_second_task(dead_event: str) -> RunState:
    s = _state(["bad", "good"])
    _task_start(s, "t1", "First")
    _result(s, dead_event, "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")
    _task_start(s, "t2", "Second")
    return s


@pytest.mark.parametrize("dead_event", ["v2_runner_on_failed", "v2_runner_on_unreachable"])
def test_dropped_host_not_synthesised_onto_later_task(dead_event: str) -> None:
    s = _run_until_second_task(dead_event)

    assert sorted(s.plays["p"].tasks["t2"].hosts) == ["good"]
    assert s.plays["p"].tasks["t2"].hosts["good"].status == Status.RUNNING


def test_failed_host_keeps_no_fabricated_ok_during_run_and_after_stats() -> None:
    """The issue reproduction: bad must not be shown running Second and
    must not gain an OK it never earned — neither mid-run nor after stats."""
    s = _run_until_second_task("v2_runner_on_failed")
    _result(s, "v2_runner_on_ok", "t2", "good")

    during = _rows(s)
    assert during["bad"].current_task is None
    assert during["bad"].counts.get(Status.OK, 0) == 0
    assert during["bad"].counts.get(Status.FAILED, 0) == 1

    _task_start(s, "t3", "Third")  # next-task cleanup must not flip bad either
    _result(s, "v2_runner_on_ok", "t3", "good")
    s.handle_event(
        {"_event": "v2_playbook_on_stats", "stats": {"bad": {"failures": 1}, "good": {"ok": 3}}}
    )

    after = _rows(s)
    assert after["bad"].counts.get(Status.OK, 0) == 0
    assert after["bad"].counts.get(Status.FAILED, 0) == 1
    assert after["bad"].failed_task == "First"
    assert after["good"].counts.get(Status.OK, 0) == 3


def test_ignore_errors_failure_keeps_host_active() -> None:
    s = _state(["bad", "good"])
    _task_start(s, "t1", "First")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom", ignore_errors=True)
    _result(s, "v2_runner_on_ok", "t1", "good")
    _task_start(s, "t2", "Second")

    assert sorted(s.plays["p"].tasks["t2"].hosts) == ["bad", "good"]


def test_host_with_later_real_result_is_synthesised_again() -> None:
    """Rescue: the failed host runs the rescue task (its result arrives
    even though it was not synthesised) and is active again afterwards."""
    s = _state(["bad", "good"])
    _task_start(s, "t1", "Block task")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")
    _task_start(s, "r1", "Rescue task")
    _result(s, "v2_runner_on_ok", "r1", "bad")
    _task_start(s, "t2", "After block")

    t2 = s.plays["p"].tasks["t2"]
    assert sorted(t2.hosts) == ["bad", "good"]
    assert t2.hosts["bad"].status == Status.RUNNING


def test_unseen_preflight_target_is_still_synthesised() -> None:
    """A target with no result yet (e.g. first task) is synthesised."""
    s = _state(["bad", "good"])
    _task_start(s, "t1", "First")

    assert sorted(s.plays["p"].tasks["t1"].hosts) == ["bad", "good"]


@pytest.mark.parametrize("dead_event", ["v2_runner_on_failed", "v2_runner_on_unreachable"])
def test_dropped_host_not_synthesised_into_subsequent_play(dead_event: str) -> None:
    """Ansible drops failed/unreachable hosts across the whole playbook run;
    a later play must not synthesise or fabricate OKs for them either."""
    s = RunState(playbook="test.yml")
    s.definitions = [
        PlayDefinition("1", "Play One", "all", resolved_hosts=["bad", "good"]),
        PlayDefinition("2", "Play Two", "all", resolved_hosts=["bad", "good"]),
    ]
    s.handle_event(
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "Play One"}}
    )
    _task_start(s, "t1", "First play task")
    _result(s, dead_event, "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")

    s.handle_event(
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p2", "name": "Play Two"}}
    )
    _task_start(s, "t2", "Second play first")
    assert sorted(s.plays["p2"].tasks["t2"].hosts) == ["good"]

    _result(s, "v2_runner_on_ok", "t2", "good")
    _task_start(s, "t3", "Second play second")
    assert sorted(s.plays["p2"].tasks["t3"].hosts) == ["good"]
    _result(s, "v2_runner_on_ok", "t3", "good")
    s.handle_event(
        {"_event": "v2_playbook_on_stats", "stats": {"bad": {"failures": 1}, "good": {"ok": 3}}}
    )

    after = _rows(s)
    assert after["bad"].counts.get(Status.OK, 0) == 0
    assert after["good"].counts.get(Status.OK, 0) == 3


def test_rescue_task_does_not_fabricate_ok_for_healthy_host() -> None:
    """In a partial-failure block, only the failed host runs the rescue task;
    the healthy host's synthesised RUNNING guess on the rescue task must be
    purged rather than swept to a fabricated OK."""
    s = _state(["bad", "good"])
    _task_start(s, "t1", "Block task")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")
    _task_start(s, "r1", "Rescue task")
    _result(s, "v2_runner_on_ok", "r1", "bad")
    _task_start(s, "t2", "After block")
    _result(s, "v2_runner_on_ok", "t2", "bad")
    _result(s, "v2_runner_on_ok", "t2", "good")
    s.handle_event(
        {"_event": "v2_playbook_on_stats", "stats": {"bad": {"ok": 2}, "good": {"ok": 2}}}
    )

    assert sorted(s.plays["p"].tasks["r1"].hosts) == ["bad"]
    rows = _rows(s)
    assert rows["good"].counts.get(Status.OK, 0) == 2
    assert rows["bad"].counts.get(Status.OK, 0) == 2
    assert rows["bad"].counts.get(Status.FAILED, 0) == 1


def test_rescue_task_definition_synthesises_only_failed_hosts() -> None:
    """When preflight marks a task as a rescue task (is_rescue=True), only
    hosts whose latest status is FAILED are synthesised as RUNNING on it."""
    s = RunState(playbook="test.yml")
    s.definitions = [
        PlayDefinition(
            "1",
            "Deploy",
            "all",
            resolved_hosts=["bad", "good"],
            tasks=[
                TaskDefinition("Block task", None, [], "1", 0, 0),
                TaskDefinition("Rescue task", None, [], "1", 0, 1, is_rescue=True),
                TaskDefinition("After block", None, [], "1", 0, 2),
            ],
        )
    ]
    s.handle_event({"_event": "v2_playbook_on_play_start", "play": {"id": "p", "name": "Deploy"}})
    _task_start(s, "t1", "Block task")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")

    _task_start(s, "r1", "Rescue task")
    assert sorted(s.plays["p"].tasks["r1"].hosts) == ["bad"]
    assert s.plays["p"].tasks["r1"].hosts["bad"].status == Status.RUNNING


def test_yaml_rescue_section_stamps_is_rescue_on_preflight_stub(tmp_path: Path) -> None:
    """Preflight YAML scanning marks tasks inside a block's rescue: section
    with is_rescue=True while leaving block: and always: tasks False."""
    playbook = tmp_path / "site.yml"
    playbook.write_text(
        "- name: Deploy\n"
        "  hosts: all\n"
        "  tasks:\n"
        "    - block:\n"
        "        - name: Block task\n"
        "          ansible.builtin.debug:\n"
        "            msg: block\n"
        "      rescue:\n"
        "        - name: Rescue task\n"
        "          ansible.builtin.debug:\n"
        "            msg: rescue\n"
        "      always:\n"
        "        - name: Always task\n"
        "          ansible.builtin.debug:\n"
        "            msg: always\n"
    )
    t_block = TaskDefinition("Block task", None, [], "1", 0, 0)
    t_rescue = TaskDefinition("Rescue task", None, [], "1", 0, 1)
    t_always = TaskDefinition("Always task", None, [], "1", 0, 2)
    defs = [
        PlayDefinition(
            "1",
            "Deploy",
            "all",
            resolved_hosts=["bad", "good"],
            tasks=[t_block, t_rescue, t_always],
        )
    ]

    graft_include_children(playbook_path=playbook, definitions=defs, cache={})

    assert t_block.is_rescue is False
    assert t_rescue.is_rescue is True
    assert t_always.is_rescue is False


def test_play_dead_hosts_and_pending_count_reactivate_rescued_host() -> None:
    """Once a failed host is rescued by a later task, play_dead_hosts and
    _pending_host_count must treat it as alive again."""
    s = _state(["bad", "good"])
    _task_start(s, "t1", "Block task")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")
    assert play_dead_hosts(s.plays["p"]) == {"bad"}

    _task_start(s, "r1", "Rescue task")
    _result(s, "v2_runner_on_ok", "r1", "bad")
    assert play_dead_hosts(s.plays["p"]) == set()

    # Under a throttled/free task where only good has started so far,
    # rescued bad must count as pending again.
    s.plays["p"].detected_strategy = "free"
    s.handle_event(
        {"_event": "v2_runner_on_start", "task": {"id": "t2", "name": "Next"}, "host": "good"}
    )
    assert _pending_host_count(s.plays["p"], s.definitions[0], s.plays["p"].tasks["t2"]) == 1


def test_tree_does_not_project_dead_hosts_when_runtime_hosts_empty() -> None:
    """When a running task has empty runtime.hosts (e.g. run_once or all
    targets dropped), TreeProjection must not fall back to projecting dead
    hosts as RUNNING leaves."""
    s = RunState(playbook="test.yml")
    s.definitions = [
        PlayDefinition(
            "1",
            "Deploy",
            "all",
            resolved_hosts=["bad", "good"],
            tasks=[
                TaskDefinition("First", None, [], "1", 0, 0),
                TaskDefinition("Once", None, [], "1", 0, 1, run_once=True),
            ],
        )
    ]
    s.handle_event({"_event": "v2_playbook_on_play_start", "play": {"id": "p", "name": "Deploy"}})
    _task_start(s, "t1", "First")
    _result(s, "v2_runner_on_failed", "t1", "bad", msg="boom")
    _result(s, "v2_runner_on_ok", "t1", "good")
    _task_start(s, "t2", "Once")

    assert s.plays["p"].tasks["t2"].hosts == {}
    lines = TreeProjection.from_run_state(s).tree_lines(budget=25)
    host_labels = [ln.label for ln in lines if ln.kind == "host"]
    assert host_labels == ["good"]
