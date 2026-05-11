"""Tests for semantic SGR colouring in the compact status output.

Colour rules (when ``colorize=True``):
- Playbook path, separators, elapsed: dim
- Completed counters (X==Y, X>0): green
- Warning glyph + count: yellow
- Deprecation glyph + count: magenta
- Final-state indicator: green / red / yellow per state
- Per-host "● N ok": green
- Per-host "◆ N changed": yellow
- Per-host "✖ N failed": red
- Per-host "⊝ N unreachable": magenta
- Failure recap labels: red (FAILED) / magenta (UNREACHABLE)

``colorize=False`` (the default) keeps the output free of escape
codes so existing snapshot-style tests and non-TTY consumers see
plain strings.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from ansible_aom.compact.renderer import (
    CompactRenderer,
    _GREEN,
    _MAGENTA,
    _RED,
    _RESET,
    _YELLOW,
    _color_enabled,
    format_failure_recap,
    format_host_summary,
    format_status_bar,
)
from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    RunState,
    Status,
    TaskRunState,
)


class TestColorEnabled:
    """The gating predicate honours both the TTY flag and ``NO_COLOR``."""

    def test_off_when_not_a_tty(self, monkeypatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert _color_enabled(is_tty=False) is False

    def test_off_when_no_color_set_even_for_tty(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert _color_enabled(is_tty=True) is False

    def test_on_when_tty_and_no_color_unset(self, monkeypatch):
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert _color_enabled(is_tty=True) is True


class TestStatusBarColors:
    """``format_status_bar(colorize=True)`` wraps semantic segments."""

    def test_default_no_color(self):
        line = format_status_bar("site.yml", 1, 2, 0, 0, 30.0, tasks_completed=5, tasks_total=10)
        assert "\x1b[" not in line

    def test_completed_hosts_segment_is_green(self):
        line = format_status_bar("site.yml", 3, 3, 0, 0, 30.0, colorize=True)
        assert f"{_GREEN}3/3 hosts{_RESET}" in line

    def test_partial_hosts_segment_is_plain(self):
        line = format_status_bar("site.yml", 2, 3, 0, 0, 30.0, colorize=True)
        assert _GREEN not in line.split("hosts")[0]

    def test_warning_segment_is_yellow(self):
        line = format_status_bar("site.yml", 0, 1, 3, 0, 30.0, colorize=True)
        assert f"{_YELLOW}⚠ 3{_RESET}" in line

    def test_deprecation_segment_is_magenta(self):
        line = format_status_bar("site.yml", 0, 1, 0, 2, 30.0, colorize=True)
        assert f"{_MAGENTA}✱ 2{_RESET}" in line

    def test_completed_tasks_segment_is_green(self):
        line = format_status_bar(
            "site.yml",
            0,
            1,
            0,
            0,
            30.0,
            tasks_completed=10,
            tasks_total=10,
            colorize=True,
        )
        assert f"{_GREEN}10/10 tasks{_RESET}" in line


class TestHostSummaryColors:
    def test_default_no_color(self):
        line = format_host_summary("web1", 5, 0, 0, 0)
        assert "\x1b[" not in line

    def test_ok_segment_is_green(self):
        line = format_host_summary("web1", 5, 0, 0, 0, colorize=True)
        assert _GREEN in line and "5 ok" in line

    def test_changed_segment_is_yellow(self):
        line = format_host_summary("web1", 0, 3, 0, 0, colorize=True)
        assert _YELLOW in line and "3 changed" in line

    def test_failed_segment_is_red(self):
        line = format_host_summary("web1", 0, 0, 2, 0, colorize=True)
        assert _RED in line and "2 failed" in line

    def test_unreachable_segment_is_magenta(self):
        line = format_host_summary("web1", 0, 0, 0, 1, colorize=True)
        assert _MAGENTA in line and "1 unreachable" in line


class TestFailureRecapColors:
    """Recap line labels carry the same colour as the per-host count."""

    def _state_with(self, status: Status) -> RunState:
        state = RunState(playbook="t.yml")
        play = PlayRunState(play_id="p1", name="P")
        task = TaskRunState(task_id="t1", name="Install nginx")
        task.hosts["web1"] = HostRunState(hostname="web1", status=status)
        play.tasks["t1"] = task
        state.plays["p1"] = play
        return state

    def test_failed_label_is_red(self):
        lines = format_failure_recap(self._state_with(Status.FAILED), colorize=True)
        assert any(_RED in line and "FAILED" in line for line in lines)

    def test_unreachable_label_is_magenta(self):
        lines = format_failure_recap(self._state_with(Status.UNREACHABLE), colorize=True)
        assert any(_MAGENTA in line and "UNREACHABLE" in line for line in lines)

    def test_no_color_by_default(self):
        lines = format_failure_recap(self._state_with(Status.FAILED))
        assert all("\x1b[" not in line for line in lines)


class TestFinalCompletionIndicator:
    """The trailing ●/✖ indicator picks its colour from the state."""

    def _final_line(self, exit_code: int, state: str, colorize: bool = True) -> str:
        renderer = CompactRenderer(is_tty=False)
        renderer.start("test.yml", [])
        # CompactRenderer(is_tty=False) → _color_enabled=False, override.
        renderer._colorize = colorize
        buf = io.StringIO()
        with redirect_stdout(buf):
            renderer.handle_completion(exit_code, state)
        return buf.getvalue().splitlines()[0]

    def test_completed_indicator_is_green(self):
        line = self._final_line(0, "completed")
        assert _GREEN in line

    def test_failed_indicator_is_red(self):
        line = self._final_line(2, "failed")
        assert _RED in line

    def test_cancelled_indicator_is_yellow(self):
        line = self._final_line(130, "crashed")
        assert _YELLOW in line
        assert "cancelled" in line.lower()

    def test_no_color_when_disabled(self):
        line = self._final_line(0, "completed", colorize=False)
        assert "\x1b[" not in line


class TestPerEventLogColors:
    """Per-task log lines (ok/changed/fatal/unreachable/skipping) carry
    semantic colour matching ansible's stock callback. These lines are
    synthesised by AOM from JSONL events — see _emit_event_log."""

    def _renderer(self, colorize: bool = True) -> CompactRenderer:
        from unittest.mock import MagicMock

        r = CompactRenderer(is_tty=False)
        r.start("t.yml", [])
        r._colorize = colorize
        r._display = MagicMock()
        return r

    def _logged(self, renderer: CompactRenderer) -> list[str]:
        return [c.args[0] for c in renderer._display.print_log.call_args_list]

    def test_ok_line_is_green(self):
        r = self._renderer()
        r._emit_event_log({"_event": "v2_runner_on_ok", "hosts": {"web1": {"changed": False}}})
        assert any(_GREEN in line and "ok: [web1]" in line for line in self._logged(r))

    def test_changed_line_is_yellow(self):
        r = self._renderer()
        r._emit_event_log({"_event": "v2_runner_on_ok", "hosts": {"web1": {"changed": True}}})
        logged = self._logged(r)
        assert any(_YELLOW in line and "changed: [web1]" in line for line in logged)

    def test_failed_line_is_red(self):
        r = self._renderer()
        r._emit_event_log(
            {
                "_event": "v2_runner_on_failed",
                "hosts": {"web1": {"msg": "boom"}},
            }
        )
        logged = self._logged(r)
        assert any(_RED in line and "FAILED" in line and "boom" in line for line in logged)

    def test_unreachable_line_is_magenta(self):
        r = self._renderer()
        r._emit_event_log(
            {
                "_event": "v2_runner_on_unreachable",
                "hosts": {"web1": {"msg": "no route"}},
            }
        )
        logged = self._logged(r)
        assert any(
            _MAGENTA in line and "UNREACHABLE" in line and "no route" in line for line in logged
        )

    def test_skipping_line_is_cyan(self):
        """Skipped hosts are buffered (collapsed-on-flush). Force the
        mixed-task flush path to verify the per-host line is still cyan."""
        from ansible_aom.compact.renderer import _CYAN

        r = self._renderer()
        r._emit_event_log({"_event": "v2_runner_on_skipped", "hosts": {"web1": {}}})
        # Flush as individual lines (the mixed-task path).
        r._flush_pending_skips(force_individual=True)
        logged = self._logged(r)
        assert any(_CYAN in line and "skipping: [web1]" in line for line in logged)

    def test_no_color_when_renderer_colorize_off(self):
        r = self._renderer(colorize=False)
        r._emit_event_log({"_event": "v2_runner_on_ok", "hosts": {"web1": {"changed": False}}})
        logged = self._logged(r)
        assert all("\x1b[" not in line for line in logged)
