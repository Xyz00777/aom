"""Tests for task summary status counts in CompactRenderer.

When a task completes, ``_emit_previous_task_summary`` appends a
per-status count suffix like ``(2 ok)`` or ``(1 failed, 1 ok)`` to the
summary line.  The suffix honours ``--hide-state`` and uses severity
colouring (failed=red, unreachable=magenta, changed=yellow, ok=green,
skipped=cyan; non-error states dim when alongside errors).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer


def _play_start(name: str = "P", play_id: str = "p1") -> dict:
    return {"_event": "v2_playbook_on_play_start", "play": {"id": play_id, "name": name}}


def _task_start(name: str = "Task", uuid: str = "u1", play_id: str = "p1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": "2026-05-11T10:00:00Z",
        "task": {"id": uuid, "name": name},
        "play": {"id": play_id},
    }


def _ok(host: str = "web1", uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": False}},
    }


def _changed(host: str = "web1", uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"changed": True}},
    }


def _failed(host: str = "web1", uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"msg": ""}},
    }


def _unreachable(host: str = "web1", uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {"msg": ""}},
    }


def _skipped(host: str = "web1", uuid: str = "u1") -> dict:
    return {
        "_event": "v2_runner_on_skipped",
        "_timestamp": "2026-05-11T10:00:01Z",
        "task": {"id": uuid},
        "hosts": {host: {}},
    }


def _renderer(hide_states: list[str] | None = None) -> CompactRenderer:
    r = CompactRenderer(is_tty=False, hide_states=hide_states or [])
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


def _last_summary_line(r: CompactRenderer) -> str | None:
    """Return the last print_log call that contains a status suffix."""
    for call in reversed(r._display.print_log.call_args_list):
        line = call[0][0]
        if "  (" in line:
            return line
    return None


def _last_print_log(r: CompactRenderer) -> str | None:
    """Return the text of the last print_log call."""
    if r._display.print_log.call_args_list:
        return r._display.print_log.call_args_list[-1][0][0]
    return None


class TestTaskSummaryAllOk:
    def test_all_ok_shows_ok_count(self) -> None:
        """Task with all-ok hosts shows '(2 ok)' in the summary."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_ok("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "(2 ok)" in line


class TestTaskSummaryMixedFailed:
    def test_mixed_failed_ok_shows_both(self) -> None:
        """Task with 1 failed + 1 ok shows '(1 failed, 1 ok)'."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 failed" in line
        assert "1 ok" in line


class TestTaskSummaryOnlyFailed:
    def test_only_failed_shows_failed(self) -> None:
        """Task with only a failed host shows '(1 failed)'."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "(1 failed)" in line


class TestTaskSummaryChanged:
    def test_changed_ok_shows_both(self) -> None:
        """Task with 1 changed + 1 ok shows '(1 changed, 1 ok)'."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_changed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 changed" in line
        assert "1 ok" in line


class TestTaskSummaryHideState:
    def test_hide_ok_suppresses_ok_from_summary(self) -> None:
        """With --hide-state ok, ok count is excluded from the summary suffix."""
        r = _renderer(hide_states=["ok"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 failed" in line
        assert "ok" not in line

    def test_hide_ok_with_only_ok_shows_no_suffix(self) -> None:
        """With --hide-state ok and all-ok task, suffix is empty (no counts)."""
        r = _renderer(hide_states=["ok"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_ok("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        last = _last_print_log(r)
        assert last is not None
        assert "  (" not in last

    def test_hide_changed_suppresses_changed_from_summary(self) -> None:
        """With --hide-state changed, changed count is excluded."""
        r = _renderer(hide_states=["changed"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_changed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "changed" not in line
        assert "1 ok" in line

    def test_hide_skipped_suppresses_skipped(self) -> None:
        """With --hide-state skipped, skipped count is excluded."""
        r = _renderer(hide_states=["skipped"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_skipped("web1", "u1"))
        r.update_state(_skipped("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is None or "skipped" not in (line or "")

    def test_failed_always_shows_even_with_hide_state_failed(self) -> None:
        """Failed count appears even if --hide-state failed is set."""
        r = _renderer(hide_states=["failed"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 failed" in line

    def test_unreachable_always_shows_even_with_hide_state_unreachable(self) -> None:
        """Unreachable count appears even if --hide-state unreachable is set."""
        r = _renderer(hide_states=["unreachable"])
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_unreachable("web1", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 unreachable" in line


class TestTaskSummaryAllSkipped:
    def test_all_skipped_shows_skipped_count(self) -> None:
        """Task with all-skipped hosts shows '(2 skipped)'."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_skipped("web1", "u1"))
        r.update_state(_skipped("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "(2 skipped)" in line


class TestTaskSummaryUnreachable:
    def test_mixed_unreachable_ok_shows_both(self) -> None:
        """Task with 1 unreachable + 1 ok shows '(1 unreachable, 1 ok)'."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_unreachable("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "1 unreachable" in line
        assert "1 ok" in line


class TestTaskSummaryWithColors:
    def test_colored_output_has_ansi_codes(self) -> None:
        """When colorize=True, the suffix uses ANSI escape codes."""
        r = CompactRenderer(is_tty=True, hide_states=[])
        r.start("test.yml", [])
        r._display = MagicMock()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        assert "\x1b[31m" in line
        assert "\x1b[2m" in line


class TestTaskSummarySeverityOrder:
    def test_failed_before_ok_in_summary(self) -> None:
        """Failed count appears before ok in the summary."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        r.update_state(_failed("web1", "u1"))
        r.update_state(_ok("web2", "u1"))
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        line = _last_summary_line(r)
        assert line is not None
        failed_idx = line.index("failed")
        ok_idx = line.index("ok")
        assert failed_idx < ok_idx


class TestTaskSummaryNoState:
    def test_no_hosts_no_suffix(self) -> None:
        """A task with no host results produces no status suffix."""
        r = _renderer()
        r.update_state(_play_start())
        r.update_state(_task_start("Install nginx", "u1"))
        # No host events for u1 — trigger summary with next task
        r.update_state(_task_start("Next task", "u2", play_id="p1"))
        last = _last_print_log(r)
        assert last is not None
        assert "  (" not in last
