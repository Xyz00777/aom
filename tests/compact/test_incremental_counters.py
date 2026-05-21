"""TC-PERF-030..031 — incremental task counters on CompactRenderer.

``count_completed_tasks`` and ``count_total_tasks_seen`` re-walked the
entire ``RunState`` on every render. The renderer maintains its own
``_tasks_seen`` and ``_tasks_completed`` counters, bumped in the event
handlers, so the per-render cost is O(1) — the format functions stay
as the test oracle.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.format import count_completed_tasks
from ansible_aom.compact.renderer import CompactRenderer


def _task_start(uuid: str, ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": f"T-{uuid}"},
        "play": {"id": "p1"},
    }


def _runner_ok(uuid: str, hosts: list[str], ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid},
        "play": {"id": "p1"},
        "hosts": {h: {"changed": False} for h in hosts},
    }


def _runner_failed(uuid: str, hosts: list[str], ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": ts,
        "task": {"id": uuid},
        "play": {"id": "p1"},
        "hosts": {h: {"msg": "boom"} for h in hosts},
    }


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


class TestIncrementalCounters:
    def test_perf_030_counters_track_oracle(self) -> None:
        """After each event the incremental counter matches count_completed_tasks."""
        r = _renderer()
        assert r._tasks_seen == 0
        assert r._tasks_completed == 0

        # Task 1: single host, ok.
        r.update_state(_task_start("u1"))
        assert r._tasks_seen == 1
        assert r._tasks_completed == count_completed_tasks(r._state)

        r.update_state(_runner_ok("u1", ["web1"]))
        assert r._tasks_completed == count_completed_tasks(r._state)

        # Task 2: two hosts, both ok in one event.
        r.update_state(_task_start("u2"))
        assert r._tasks_seen == 2
        r.update_state(_runner_ok("u2", ["web1", "web2"]))
        assert r._tasks_completed == count_completed_tasks(r._state)

        # Task 3: failure.
        r.update_state(_task_start("u3"))
        assert r._tasks_seen == 3
        r.update_state(_runner_failed("u3", ["web1"]))
        assert r._tasks_completed == count_completed_tasks(r._state)

    def test_perf_031_dynamic_include_task_still_counts(self) -> None:
        """A task that arrives without preflight registration still increments."""
        r = _renderer()
        r.update_state(_task_start("dyn-1"))
        r.update_state(_task_start("dyn-2"))
        r.update_state(_task_start("dyn-3"))
        assert r._tasks_seen == 3

    def test_completed_counter_not_double_counted(self) -> None:
        """Re-arriving terminal events for the same task don't double-count."""
        r = _renderer()
        r.update_state(_task_start("u1"))
        r.update_state(_runner_ok("u1", ["web1"]))
        assert r._tasks_completed == 1
        # Replay the same event — must not bump the counter past 1.
        r.update_state(_runner_ok("u1", ["web1"]))
        assert r._tasks_completed == 1
