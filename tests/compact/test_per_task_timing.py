"""Tests for inline + post-task duration display.

When a task completes (any of ``v2_runner_on_*``), the synthesised
result line carries the per-host duration in parentheses:

    ok: [web1] (2.3s)

When a task completes on every target host (or the run ends), a
one-line summary of it is emitted. Under the linear strategy that
coincides with the next ``v2_playbook_on_task_start``, so the summary
lands between the previous task's output and the next ``TASK [...]``
header:

    [14:10:48] Install nginx — 2.3s (0:00:09)

Both pieces fall back gracefully when timing data is missing.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.models import PlayDefinition


def _task_start(ts: str, name: str = "Install nginx", uuid: str = "t1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": name},
        "play": {"id": "p1"},
    }


def _runner_ok(ts: str, host: str = "web1", uuid: str = "t1", changed: bool = False) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"changed": changed}},
    }


def _runner_failed(ts: str, host: str = "web1", uuid: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"msg": "boom"}},
    }


def _stats(ts: str) -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts, "stats": {}}


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._display = MagicMock()
    return r


def _state_renderer(hosts: list[str]) -> CompactRenderer:
    """Renderer wired for the completion-aware summary path: preflight
    target hosts set, driven via ``update_state`` so RunState fills in."""
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._display = MagicMock()
    r.set_definitions(
        [PlayDefinition(id="p1", name="P", hosts="all", resolved_hosts=list(hosts), tasks=[])]
    )
    r.update_state({"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": "P"}})
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


class TestInlineDuration:
    def test_ok_line_carries_seconds_duration(self):
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z"))
        r._emit_event_log(_runner_ok("2026-05-11T14:10:02.5Z"))
        # 2.5 seconds → "(2.5s)" suffix.
        assert any("ok: [web1] (2.5s)" in line for line in _logged(r))

    def test_changed_line_carries_duration(self):
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z"))
        r._emit_event_log(_runner_ok("2026-05-11T14:10:00.4Z", changed=True))
        assert any("changed: [web1] (0.4s)" in line for line in _logged(r))

    def test_failed_line_carries_duration_before_msg(self):
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z"))
        r._emit_event_log(_runner_failed("2026-05-11T14:10:01.0Z"))
        assert any(
            "fatal: [web1] (1.0s): FAILED!" in line and "boom" in line for line in _logged(r)
        )

    def test_long_duration_renders_compact(self):
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z"))
        # 75 seconds → "1m15s".
        r._emit_event_log(_runner_ok("2026-05-11T14:11:15Z"))
        assert any("(1m15s)" in line for line in _logged(r))

    def test_missing_timestamp_drops_duration_suffix(self):
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z"))
        r._emit_event_log(
            {
                "_event": "v2_runner_on_ok",
                # no _timestamp
                "task": {"id": "t1"},
                "hosts": {"web1": {"changed": False}},
            }
        )
        # No duration parenthesis appended.
        assert any("ok: [web1]" in line and "(" not in line for line in _logged(r))

    def test_unknown_task_uuid_drops_duration_suffix(self):
        """No matching task_start → no duration."""
        r = _renderer()
        r._emit_event_log(_runner_ok("2026-05-11T14:10:02.5Z", uuid="never-seen"))
        assert any("ok: [web1]" in line and "(" not in line for line in _logged(r))


class TestPreviousTaskSummary:
    def test_summary_line_lands_before_next_task_header(self):
        # Single-host linear task: it completes when its one host reports,
        # and its summary lands at the next task's announcement — before
        # that task's header, attached to its own output.
        r = _state_renderer(["web1"])
        r.update_state(_task_start("2026-05-11T14:10:00Z", name="First"))
        r.update_state(_runner_ok("2026-05-11T14:10:02.5Z"))
        r.update_state(_task_start("2026-05-11T14:10:03Z", name="Second", uuid="t2"))

        logged = _logged(r)
        # Find the summary line and verify it's BEFORE the next TASK header.
        summary_indices = [i for i, line in enumerate(logged) if "First" in line and "—" in line]
        task_header_indices = [i for i, line in enumerate(logged) if "TASK [Second]" in line]
        assert summary_indices, f"no summary line found in {logged}"
        assert task_header_indices, f"no second TASK header in {logged}"
        assert summary_indices[0] < task_header_indices[0]

    def test_summary_contains_task_duration_when_no_per_host_duration(self):
        """Hosts report without timestamps → no per-host duration shown →
        the multi-host summary keeps the task duration (start→completion)."""
        r = _state_renderer(["web1", "web2"])
        r.update_state(_task_start("2026-05-11T14:10:00Z", name="First"))
        # No _timestamp on the results → no inline per-host duration.
        r.update_state({"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"web1": {}}})
        r.update_state({"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"web2": {}}})
        r.update_state(_task_start("2026-05-11T14:10:03Z", name="Second", uuid="t2"))
        # First completes at the Second announce (14:10:03) → 3.0s duration.
        assert any("First" in line and "3.0s" in line for line in _logged(r))

    def test_summary_drops_duration_for_single_host_task(self):
        """Single-host tasks already show duration on the per-host line; the
        summary line drops it to avoid duplication."""
        r = _state_renderer(["web1"])
        r.update_state(_task_start("2026-05-11T14:10:00Z", name="First"))
        r.update_state(_runner_ok("2026-05-11T14:10:02.5Z", host="web1"))
        r.update_state(_task_start("2026-05-11T14:10:03Z", name="Second", uuid="t2"))
        # Summary for First should NOT contain the per-task duration (3.0s).
        summary_lines = [line for line in _logged(r) if "First" in line and "—" in line]
        assert summary_lines, "expected summary line for First"
        assert not any("3.0s" in line for line in summary_lines)
        # …but the per-host line still carries the inline duration.
        assert any("ok: [web1] (2.5s)" in line for line in _logged(r))

    def test_summary_keeps_duration_for_multi_host_task(self):
        """When multiple hosts ran the task, per-host durations may differ —
        the summary's task duration remains useful, so keep it."""
        r = _state_renderer(["web1", "web2"])
        r.update_state(_task_start("2026-05-11T14:10:00Z", name="First"))
        r.update_state(_runner_ok("2026-05-11T14:10:01.0Z", host="web1"))
        r.update_state(_runner_ok("2026-05-11T14:10:02.5Z", host="web2"))
        r.update_state(_task_start("2026-05-11T14:10:03Z", name="Second", uuid="t2"))
        summary_lines = [line for line in _logged(r) if "First" in line and "—" in line]
        assert summary_lines, "expected summary line for First"
        # 3.0s is the task duration (start→completion at the Second announce).
        assert any("3.0s" in line for line in summary_lines)

    def test_summary_contains_cumulative(self):
        r = _renderer()
        # Force a known _start_time so cumulative is predictable.
        r._start_time = 1000.0
        r._task_start_times["t1"] = 1000.0  # task starts at start time
        r._task_names["t1"] = "First"
        # Emit at +12s → cumulative 12s.
        r._emit_task_summary("t1", 1012.0)
        logged = _logged(r)
        assert any("(12" in line for line in logged)

    def test_summary_emitted_on_stats_for_final_task(self):
        r = _state_renderer(["web1"])
        r.update_state(_task_start("2026-05-11T14:10:00Z", name="Last"))
        r.update_state(_runner_ok("2026-05-11T14:10:01.0Z"))
        r.update_state(_stats("2026-05-11T14:10:02.0Z"))
        # The Last task should get its own summary at stats time. Single-host
        # → per-task duration is suppressed; only the cumulative remains.
        assert any("Last" in line and " — " in line for line in _logged(r))

    def test_no_summary_when_no_prior_task(self):
        """First task_start has no predecessor to summarise."""
        r = _renderer()
        r._emit_event_log(_task_start("2026-05-11T14:10:00Z", name="First"))
        # Only the TASK header should be there; no summary line yet.
        logged = _logged(r)
        assert any("TASK [First]" in line for line in logged)
        # No "— Ns" lines yet (the em-dash separator we use in summaries).
        assert not any(" — " in line and "s" in line for line in logged)


class TestFormatDuration:
    def test_sub_minute_uses_seconds(self):
        r = _renderer()
        assert r._format_duration(0.0) == "0.0s"
        assert r._format_duration(0.5) == "0.5s"
        assert r._format_duration(59.9) == "59.9s"

    def test_minute_range(self):
        r = _renderer()
        assert r._format_duration(60.0) == "1m00s"
        assert r._format_duration(75.0) == "1m15s"
        assert r._format_duration(3599.0) == "59m59s"

    def test_hour_range(self):
        r = _renderer()
        assert r._format_duration(3600.0) == "1h00m"
        assert r._format_duration(7320.0) == "2h02m"
