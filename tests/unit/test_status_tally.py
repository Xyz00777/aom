"""Unit tests for live-state status tallies (aggregate + per-host).

The compact status bar and host rows need ok/changed/skipped/failed
counts derived from a live ``RunState`` — the same numbers ``aom
inspect --text`` reports from recorded events, but computed from the
in-memory state tree so they update live.
"""

from __future__ import annotations

from ansible_aom.core.inspect_model import StatusCounts
from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)
from ansible_aom.core.tree import run_state_host_counts, run_state_status_counts


def _run_state() -> RunState:
    """A run with two hosts across three tasks, mixed outcomes.

    web1: task A ok, task B changed, task C failed
    web2: task A ok, task B ok(+changed flag), task C skipped
    A third host state on task A is still RUNNING and must not count.
    """
    play = PlayRunState(play_id="1", name="play")
    play.tasks["a"] = TaskRunState(
        task_id="a",
        name="A",
        hosts={
            "web1": HostRunState(hostname="web1", status=Status.OK),
            "web2": HostRunState(hostname="web2", status=Status.OK),
            "web3": HostRunState(hostname="web3", status=Status.RUNNING),
        },
    )
    play.tasks["b"] = TaskRunState(
        task_id="b",
        name="B",
        hosts={
            "web1": HostRunState(hostname="web1", status=Status.CHANGED),
            # OK + changed flag must be promoted to CHANGED (effective status).
            "web2": HostRunState(hostname="web2", status=Status.OK, changed=True),
        },
    )
    play.tasks["c"] = TaskRunState(
        task_id="c",
        name="C",
        hosts={
            "web1": HostRunState(hostname="web1", status=Status.FAILED),
            "web2": HostRunState(hostname="web2", status=Status.SKIPPED),
        },
    )
    return RunState(playbook="site.yml", plays={"1": play})


def test_aggregate_status_counts() -> None:
    counts = run_state_status_counts(_run_state())
    # ok: web1/A, web2/A  -> 2
    # changed: web1/B, web2/B(promoted) -> 2
    # failed: web1/C -> 1
    # skipped: web2/C -> 1
    # RUNNING web3/A excluded.
    assert counts == StatusCounts(ok=2, changed=2, failed=1, skipped=1, unreachable=0)


def test_per_host_status_counts() -> None:
    per_host = run_state_host_counts(_run_state())
    assert per_host["web1"] == StatusCounts(ok=1, changed=1, failed=1)
    assert per_host["web2"] == StatusCounts(ok=1, changed=1, skipped=1)
    # web3 only ever RUNNING -> contributes no terminal counts.
    assert "web3" not in per_host


def test_unreachable_counted() -> None:
    play = PlayRunState(play_id="1", name="play")
    play.tasks["a"] = TaskRunState(
        task_id="a",
        name="A",
        hosts={"db1": HostRunState(hostname="db1", status=Status.UNREACHABLE)},
    )
    state = RunState(playbook="site.yml", plays={"1": play})
    assert run_state_status_counts(state) == StatusCounts(unreachable=1)
