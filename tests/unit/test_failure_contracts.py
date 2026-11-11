"""Failure contracts that need mixed results to distinguish plausible regressions."""

import pytest

from ansible_aom.core.exit_code import determine_exit_code
from ansible_aom.core.models import HostRunState, PlayRunState, Status, TaskRunState
from ansible_aom.core.run_state import RunState


@pytest.mark.parametrize("failure_location", ["same-task", "later-task", "later-play"])
def test_failed_result_overrides_an_earlier_unreachable_result(failure_location: str) -> None:
    # A single traversal that returns on the first error loses FAILED precedence.
    state = RunState(playbook="mixed.yml")
    first_play = PlayRunState(play_id="connect", name="Connect")
    first_task = TaskRunState(task_id="probe", name="Probe")
    first_task.hosts["offline"] = HostRunState(hostname="offline", status=Status.UNREACHABLE)
    first_play.tasks["probe"] = first_task
    state.plays["connect"] = first_play

    if failure_location == "same-task":
        failing_task = first_task
    elif failure_location == "later-task":
        failing_task = TaskRunState(task_id="deploy", name="Deploy")
        first_play.tasks["deploy"] = failing_task
    else:
        next_play = PlayRunState(play_id="configure", name="Configure")
        failing_task = TaskRunState(task_id="configure-service", name="Configure service")
        next_play.tasks["configure-service"] = failing_task
        state.plays["configure"] = next_play
    failing_task.hosts["broken"] = HostRunState(hostname="broken", status=Status.FAILED)

    assert determine_exit_code(state) == 1


@pytest.mark.parametrize("ignored_first", [True, False])
def test_ignore_errors_is_scoped_to_each_host_result(ignored_first: bool) -> None:
    # Reading the first result's marker for the whole callback event hides a real
    # failure or invents one for another host; singleton fixtures cannot catch it.
    state = RunState(playbook="mixed.yml")
    state.handle_event(
        {"_event": "v2_playbook_on_play_start", "play": {"id": "p", "name": "Deploy"}}
    )
    state.handle_event(
        {"_event": "v2_playbook_on_task_start", "task": {"id": "t", "name": "Probe"}}
    )
    hosts = {
        "optional": {"failed": True, "ignore_errors": True, "msg": "optional probe"},
        "required": {"failed": True, "ignore_errors": False, "msg": "required probe"},
    }
    if not ignored_first:
        hosts = dict(reversed(list(hosts.items())))
    state.handle_event({"_event": "v2_runner_on_failed", "task": {"id": "t"}, "hosts": hosts})

    results = state.plays["p"].tasks["t"].hosts
    assert {host: (result.status, result.message) for host, result in results.items()} == {
        "optional": (Status.OK, "optional probe"),
        "required": (Status.FAILED, "required probe"),
    }
    assert state.status == Status.FAILED
    assert determine_exit_code(state) == 1
