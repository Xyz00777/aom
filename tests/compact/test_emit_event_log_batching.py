"""TC-PERF-001..002 — batched print_log per runner event.

A single runner event (``v2_runner_on_ok``, ``v2_runner_on_failed``,
``v2_runner_on_unreachable``) carrying N hosts must produce exactly
one ``Display.print_log`` call with the N per-host lines joined by
``\\n``, not N separate calls. Each ``print_log`` rewinds and rewrites
the status panel — calling it once per host is the dominant stdout
cost on multi-host runs.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer


def _task_start(uuid: str = "u1", ts: str = "2026-05-11T10:00:00Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "T"},
        "play": {"id": "p1"},
    }


def _runner_ok_multi(hosts: list[str], uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": False} for host in hosts},
    }


def _runner_failed_multi(hosts: list[str], uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"msg": "boom"} for host in hosts},
    }


def _runner_unreachable_multi(hosts: list[str], uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"msg": "no ssh"} for host in hosts},
    }


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


def _print_log_calls(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


class TestRunnerOkBatching:
    def test_perf_001_one_print_log_call_per_event(self):
        """14 hosts in one ok event → exactly one print_log call."""
        r = _renderer()
        r._emit_event_log(_task_start())
        # Reset the spy so we only count post-task-start log calls.
        r._display.reset_mock()

        hosts = [f"web{i}" for i in range(14)]
        r._emit_event_log(_runner_ok_multi(hosts))

        assert r._display.print_log.call_count == 1

    def test_perf_002_all_host_lines_present_in_single_call(self):
        """The single print_log argument carries every host line."""
        r = _renderer()
        r._emit_event_log(_task_start())
        r._display.reset_mock()

        hosts = [f"web{i}" for i in range(14)]
        r._emit_event_log(_runner_ok_multi(hosts))

        (single_call,) = r._display.print_log.call_args_list
        payload: str = single_call.args[0]
        for host in hosts:
            assert f"ok: [{host}]" in payload
        # Lines are joined; a 14-host event produces a 14-line block
        # (the trailing newline added by Display.print_log is not in
        # the message we pass).
        assert payload.count("\n") == 13


class TestRunnerFailedBatching:
    def test_failed_event_batched(self):
        r = _renderer()
        r._emit_event_log(_task_start())
        r._display.reset_mock()

        r._emit_event_log(_runner_failed_multi(["web1", "web2", "web3"]))

        assert r._display.print_log.call_count == 1
        payload: str = _print_log_calls(r)[0]
        for host in ("web1", "web2", "web3"):
            assert f"fatal: [{host}]" in payload
            assert "FAILED!" in payload


class TestRunnerUnreachableBatching:
    def test_unreachable_event_batched(self):
        r = _renderer()
        r._emit_event_log(_task_start())
        r._display.reset_mock()

        r._emit_event_log(_runner_unreachable_multi(["web1", "web2"]))

        assert r._display.print_log.call_count == 1
        payload: str = _print_log_calls(r)[0]
        for host in ("web1", "web2"):
            assert f"fatal: [{host}]" in payload
            assert "UNREACHABLE!" in payload


class TestRunnerOkMixedChanged:
    def test_changed_and_ok_hosts_in_one_call(self):
        """ok event with some hosts changed=True still produces one call."""
        r = _renderer()
        r._emit_event_log(_task_start())
        r._display.reset_mock()

        event = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-05-11T10:00:01Z",
            "task": {"id": "u1"},
            "hosts": {
                "web1": {"changed": True},
                "web2": {"changed": False},
            },
        }
        r._emit_event_log(event)

        assert r._display.print_log.call_count == 1
        payload: str = _print_log_calls(r)[0]
        assert "changed: [web1]" in payload
        assert "ok: [web2]" in payload


class TestStderrLineRendering:
    """aom_stderr_line events must render in the live compact log.

    SPECIFICATION.md (Stderr Capture): "Display stderr lines in log panel
    (TUI) or console (compact)". AOM records non-warning stderr as
    synthetic aom_stderr_line events; the compact renderer must print
    them so real stderr output (module output, profiling-callback
    banners) is visible live, not silently dropped.
    """

    def _stderr_line(self, text: str, source: str = "run_level") -> dict:
        return {
            "_event": "aom_stderr_line",
            "_timestamp": "2026-05-11T10:00:01Z",
            "line": text,
            "source": source,
            "level": 1,
        }

    def test_stderr_line_prints_to_log(self):
        r = _renderer()
        r._emit_event_log(self._stderr_line("some stderr text"))

        assert r._display.print_log.call_count == 1
        payload: str = _print_log_calls(r)[0]
        assert "some stderr text" in payload

    def test_profile_tasks_banner_line_is_suppressed_in_compact_view(self):
        """Redundant profile_tasks / timer banners from third-party callbacks
        must be suppressed from the live compact view to avoid duplicate clutter."""
        r = _renderer()
        german_banner = (
            "Dienstag 04 August 2026  19:02:51 +0200 (0:00:00.477)       0:00:00.477 *******"
        )
        r._emit_event_log(self._stderr_line(german_banner))
        assert r._display.print_log.call_count == 0

        english_banner = (
            "Tuesday 04 August 2026  19:02:51 +0200 (0:00:00.025)       0:00:00.025 *******"
        )
        r._emit_event_log(self._stderr_line(english_banner))
        assert r._display.print_log.call_count == 0

    def test_stderr_line_with_ansi_escapes_is_stripped(self):
        r = _renderer()
        raw = "\x1b[1;35m[WARNING]\x1b[0m some text"
        r._emit_event_log(self._stderr_line(raw, source="warning"))

        payload: str = _print_log_calls(r)[0]
        assert "\x1b[" not in payload
        assert "some text" in payload

    def test_blank_stderr_line_is_silent(self):
        """Empty/whitespace-only stderr lines produce no log noise."""
        r = _renderer()
        r._emit_event_log(self._stderr_line("   "))

        assert r._display.print_log.call_count == 0
