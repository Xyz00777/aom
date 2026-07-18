"""Per-event cost of the full-completion summary sweep must stay flat.

Regression for the compact-view freeze under ``strategy: free``: after
98d0c40 every terminal runner event swept *all* announced-but-incomplete
tasks through ``task_complete_on_all_targets`` — which itself rebuilds
the play-wide dead-host set (all tasks × hosts) per call. With one
straggler host pinning the pending list open, per-event cost grew
linearly with run progress (quadratic overall) until the single-threaded
display loop could no longer drain the PTY: the panel froze mid-run and
ansible eventually stalled on the full PTY buffer.

A task can only newly complete via one of its OWN terminal events or a
host death (failed/unreachable shrinks the live-target set), so the
completion check must be event-scoped: O(1) checks on ordinary events,
with the full pending sweep reserved for (rare) death events.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import ansible_aom.compact.renderer as renderer_mod
from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition


def _renderer(hosts: list[str]) -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    r.set_definitions(
        [PlayDefinition(id="p1", name="P", hosts="all", resolved_hosts=list(hosts), tasks=[])]
    )
    r.update_state({"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "P"}})
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


def _summary_lines(r: CompactRenderer, name: str) -> list[str]:
    return [line for line in _logged(r) if name in line and " — " in line]


TS = "2026-05-11T10:00:00Z"


def _start(task_id: str, host: str, name: str | None = None) -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": TS,
        "task": {"id": task_id, "name": name or f"task {task_id}"},
        "play": {"id": "p1"},
        "host": host,
    }


def _ok(task_id: str, host: str, name: str | None = None) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": TS,
        "task": {"id": task_id, "name": name or f"task {task_id}"},
        "play": {"id": "p1"},
        "hosts": {host: {"changed": False}},
    }


def _failed(task_id: str, host: str) -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": TS,
        "task": {"id": task_id, "name": f"task {task_id}"},
        "play": {"id": "p1"},
        "hosts": {host: {"msg": "boom"}},
    }


def _unreachable(task_id: str, host: str) -> dict:
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": TS,
        "task": {"id": task_id, "name": f"task {task_id}"},
        "play": {"id": "p1"},
        "hosts": {host: {"msg": "unreachable"}},
    }


def test_completion_checks_stay_linear_with_a_straggler_host(monkeypatch) -> None:
    """One slow host must not make per-event completion checks sweep the
    whole pending backlog. Bound: O(1) checks per event, not O(pending)."""
    calls = 0
    real = renderer_mod.task_complete_on_all_targets

    def counting(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real(*args, **kwargs)

    monkeypatch.setattr(renderer_mod, "task_complete_on_all_targets", counting)

    n_tasks = 150
    r = _renderer(["fast", "slow"])
    # The straggler starts the first task and never reports again.
    r.update_state(_start("t0000", "slow"))
    for i in range(1, n_tasks + 1):
        tid = f"t{i:04d}"
        r.update_state(_start(tid, "fast"))
        r.update_state(_ok(tid, "fast"))

    # ~2 events per task; allow a small constant factor of checks per
    # event. The quadratic sweep performed ~n_tasks²/2 calls (>10 000).
    assert calls <= 4 * n_tasks, f"completion checks swept the backlog: {calls} calls"
    # Nothing may have been summarised — the straggler blocks every task.
    assert not [line for line in _logged(r) if " — " in line]


def test_host_death_flushes_other_pending_tasks() -> None:
    """A host dying in one task completes OTHER tasks it was blocking:
    dead hosts leave the live-target set, so an earlier task whose only
    missing result was from the dead host must summarise at that moment."""
    r = _renderer(["a", "b"])
    r.update_state(_start("t1", "a", "First"))
    r.update_state(_ok("t1", "a", "First"))
    # b never reports First (divergent include path), goes on to Second.
    r.update_state(_start("t2", "a", "Second"))
    r.update_state(_start("t2", "b", "Second"))
    assert not _summary_lines(r, "First")
    r.update_state(_unreachable("t2", "b"))
    # b is dead → First's live targets shrink to {a} → complete.
    assert len(_summary_lines(r, "First")) == 1, _logged(r)


def test_revived_host_blocks_completion_again() -> None:
    """A host whose FAILED result is later overwritten by an OK (retry /
    async-poll recovery) is alive again and must block completion of
    later tasks it has not reached — any cached dead-host view must not
    go stale."""
    r = _renderer(["a", "b"])
    r.update_state(_start("t1", "a", "First"))
    r.update_state(_start("t1", "b", "First"))
    r.update_state(_ok("t1", "a", "First"))
    r.update_state(_failed("t1", "b"))
    # b dead → Second completes on a alone.
    r.update_state(_start("t2", "a", "Second"))
    r.update_state(_ok("t2", "a", "Second"))
    r.update_state(_start("t3", "a", "Third"))
    assert len(_summary_lines(r, "Second")) == 1, _logged(r)
    # b's First retry lands OK, overwriting the FAILED entry — revived.
    r.update_state(_ok("t1", "b", "First"))
    r.update_state(_ok("t3", "a", "Third"))
    r.update_state(_start("t4", "a", "Fourth"))
    # Third must NOT summarise: b is alive again and hasn't run it.
    assert not _summary_lines(r, "Third"), _logged(r)
