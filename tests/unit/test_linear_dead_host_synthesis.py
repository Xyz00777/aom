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

import pytest

from ansible_aom.core.models import PlayDefinition, RunState, Status
from ansible_aom.core.tree_projection import HostRow, TreeProjection


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
