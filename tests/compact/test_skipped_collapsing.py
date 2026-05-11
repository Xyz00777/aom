"""Tests for skipped-task collapsing.

When a task produces only ``skipped`` results, the per-host
``skipping: [...]`` lines collapse to one summary line:

    … 3 hosts skipped: web1, web2, web3   (≤3 hosts: list them)
    … 12 hosts skipped                    (>3: count only)

When a task has mixed results (some skipped + some ok/changed/failed),
the buffered skipped lines flush individually so the user gets full
per-host detail.

Flush points:
- Next ``v2_playbook_on_task_start`` (transition between tasks)
- ``v2_playbook_on_stats`` (final task)
- Any non-skipped result for the *same* task (mixed case)
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import _CYAN, CompactRenderer


def _task_start(name: str = "T", uuid: str = "u", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": name},
        "play": {"id": "p1"},
    }


def _skipped(host: str, uuid: str = "u", ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_skipped",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {}},
    }


def _ok(host: str, uuid: str = "u", ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"changed": False}},
    }


def _stats(ts: str = "2026-05-11T10:00:02Z") -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts, "stats": {}}


def _renderer(colorize: bool = False) -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = colorize
    r._display = MagicMock()
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


class TestAllSkippedCollapsing:
    def test_three_or_fewer_hosts_lists_names(self):
        r = _renderer()
        r._emit_event_log(_task_start("Configure things", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        # Flush via next task start.
        r._emit_event_log(_task_start("Next task", "u2"))

        logged = _logged(r)
        assert not any("skipping: [web1]" in line for line in logged)
        assert not any("skipping: [web2]" in line for line in logged)
        assert any("2 hosts skipped" in line and "web1" in line and "web2" in line for line in logged)

    def test_many_hosts_shows_count_only(self):
        r = _renderer()
        r._emit_event_log(_task_start("Configure", "u1"))
        for i in range(8):
            r._emit_event_log(_skipped(f"web{i}", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))

        logged = _logged(r)
        # Single compressed line; no per-host names listed.
        compressed = [line for line in logged if "8 hosts skipped" in line]
        assert len(compressed) == 1
        # Names of all individual hosts NOT in any line — compression succeeded.
        for i in range(8):
            assert not any(f"web{i}" in line for line in compressed)

    def test_single_skipped_host_singular_form(self):
        r = _renderer()
        r._emit_event_log(_task_start("Configure", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))

        logged = _logged(r)
        assert any("1 host skipped" in line and "web1" in line for line in logged)

    def test_compressed_line_is_cyan(self):
        r = _renderer(colorize=True)
        r._emit_event_log(_task_start("Configure", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))

        logged = _logged(r)
        assert any(_CYAN in line and "skipped" in line for line in logged)

    def test_collapse_at_stats_for_final_task(self):
        """The very last task can't be flushed by a next task_start;
        the stats event must trigger the same collapse."""
        r = _renderer()
        r._emit_event_log(_task_start("Last task", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_stats())

        logged = _logged(r)
        assert any("2 hosts skipped" in line for line in logged)


class TestMixedTaskExpandsIndividually:
    def test_skipped_then_ok_expands_skipped_lines(self):
        r = _renderer()
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        # Non-skipped result arrives → flush buffered as individuals.
        r._emit_event_log(_ok("web3", "u1"))

        logged = _logged(r)
        # Individual skip lines now visible.
        assert any("skipping: [web1]" in line for line in logged)
        assert any("skipping: [web2]" in line for line in logged)
        # And the ok line.
        assert any("ok: [web3]" in line for line in logged)
        # NO compressed line.
        assert not any("hosts skipped" in line for line in logged)

    def test_ok_then_skipped_only_flushed_at_transition(self):
        """ok arrives first, then skipped — those skipped land at the
        next task transition. Since they have no non-skipped sibling
        after, the flush is the *mixed* path because the task as a
        whole had a non-skipped result."""
        r = _renderer()
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))

        logged = _logged(r)
        assert any("ok: [web1]" in line for line in logged)
        # Individual skip line — mixed task expands.
        assert any("skipping: [web2]" in line for line in logged)
        assert not any("hosts skipped" in line for line in logged)


class TestStateResetBetweenTasks:
    def test_collapsing_state_does_not_leak_to_next_task(self):
        """All-skipped task A followed by mixed task B: B must
        flush its own skips individually, not see A's state."""
        r = _renderer()
        r._emit_event_log(_task_start("A", "ua"))
        r._emit_event_log(_skipped("h1", "ua"))
        r._emit_event_log(_skipped("h2", "ua"))
        # Transition.
        r._emit_event_log(_task_start("B", "ub"))
        r._emit_event_log(_skipped("h3", "ub"))
        r._emit_event_log(_ok("h4", "ub"))

        logged = _logged(r)
        # A compressed.
        assert any("2 hosts skipped" in line and "h1" in line for line in logged)
        # B expanded.
        assert any("skipping: [h3]" in line for line in logged)
        assert any("ok: [h4]" in line for line in logged)
