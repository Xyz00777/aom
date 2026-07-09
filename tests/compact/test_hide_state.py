"""Tests for --hide-state gating in CompactRenderer._emit_event_log.

When hide_states contains a state name, the corresponding per-host
result lines are suppressed from the live log. The status panel,
event recording, and aom inspect are unaffected.

Gated branches:
- v2_runner_on_ok (suppresses ok: and changed: lines)
- v2_runner_on_failed (suppresses fatal: FAILED! lines)
- v2_runner_on_unreachable (suppresses fatal: UNREACHABLE! lines)
- v2_runner_on_skipped (suppresses skipping: lines)
- v2_runner_item_on_* (suppresses per-item loop lines)

Never gated:
- v2_playbook_on_play_start (PLAY header)
- v2_playbook_on_task_start (TASK header)
- v2_runner_on_start
- v2_playbook_on_stats
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer
from ansible_aom.core.run_state import RunState


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


def _changed(host: str, uuid: str = "u", ts: str = "2026-05-11T10:00:01Z") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"changed": True}},
    }


def _failed(host: str, uuid: str = "u", ts: str = "2026-05-11T10:00:01Z", msg: str = "") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"msg": msg}},
    }


def _unreachable(
    host: str, uuid: str = "u", ts: str = "2026-05-11T10:00:01Z", msg: str = ""
) -> dict:
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: {"msg": msg}},
    }


def _play_start(name: str = "P") -> dict:
    return {"_event": "v2_playbook_on_play_start", "play": {"id": "p1", "name": name}}


def _stats(ts: str = "2026-05-11T10:00:02Z") -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts, "stats": {}}


def _renderer(
    hide_states: list[str] | None = None, show_failed_hint: bool = True
) -> CompactRenderer:
    r = CompactRenderer(
        is_tty=False,
        hide_states=hide_states or [],
        show_failed_hint=show_failed_hint,
    )
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


def _logged(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


class TestHideOk:
    def test_ok_lines_are_suppressed(self):
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [web1]" in line for line in logged)

    def test_changed_lines_still_print_when_ok_hidden(self):
        """Hiding only 'ok' must NOT suppress 'changed:' lines — they are
        distinct per-host states within v2_runner_on_ok."""
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_changed("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("changed: [web1]" in line for line in logged), (
            f"'changed:' lines should print when only 'ok' is hidden, got: {logged}"
        )

    def test_task_header_still_prints(self):
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_task_start("Install nginx", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("Install nginx" in line for line in logged)

    def test_play_header_still_prints(self):
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_play_start("Deploy"))
        logged = _logged(r)
        assert any("PLAY [Deploy]" in line for line in logged)

    def test_skipped_lines_still_print_when_ok_hidden(self):
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("skipping: [web2]" in line for line in logged)


class TestHideChanged:
    """Hiding 'changed' suppresses ONLY changed: lines, NOT ok: lines.

    The per-host ``result.changed`` field determines whether a host is
    ok or changed — ``--hide-state changed`` must NOT suppress ok: lines
    from the same v2_runner_on_ok event.
    """

    def test_changed_lines_are_suppressed(self):
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_changed("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("changed: [web1]" in line for line in logged), (
            f"--hide-state changed should suppress 'changed:' lines, got: {logged}"
        )

    def test_ok_lines_still_print_when_changed_hidden(self):
        """Hiding only 'changed' must NOT suppress 'ok:' lines — they are
        distinct per-host states within v2_runner_on_ok."""
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("ok: [web1]" in line for line in logged), (
            f"'ok:' lines should print when only 'changed' is hidden, got: {logged}"
        )

    def test_task_header_still_prints(self):
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("Install nginx", "u1"))
        r._emit_event_log(_changed("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("Install nginx" in line for line in logged)

    def test_failed_lines_still_print_when_changed_hidden(self):
        """Hiding only 'changed' must not affect failed/unreachable lines."""
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_failed("web1", "u1", msg="permission denied"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("FAILED" in line for line in logged)

    def test_skipped_lines_still_print_when_changed_hidden(self):
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_changed("web2", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("skipping: [web1]" in line for line in logged)


class TestHideSkipped:
    def test_skipped_lines_are_suppressed(self):
        r = _renderer(hide_states=["skipped"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("skipping" in line for line in logged)
        assert not any("skipped" in line for line in logged)

    def test_ok_lines_still_print_when_skipped_hidden(self):
        r = _renderer(hide_states=["skipped"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._emit_event_log(_ok("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("ok: [web2]" in line for line in logged)


class TestHideFailed:
    def test_failed_lines_are_suppressed(self):
        r = _renderer(hide_states=["failed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_failed("web1", "u1", msg="permission denied"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("FAILED" in line for line in logged)

    def test_ok_lines_still_print_when_failed_hidden(self):
        r = _renderer(hide_states=["failed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("ok: [web2]" in line for line in logged)


class TestHideFailedHint:
    def test_failed_hint_can_be_disabled(self):
        r = _renderer(show_failed_hint=False)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_failed("web1", "u1", msg="permission denied\nretry later"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        fatal_lines = [line for line in logged if "FAILED!" in line]
        assert fatal_lines
        assert all(" => " not in line for line in fatal_lines)

    def test_unreachable_hint_can_be_disabled(self):
        r = _renderer(show_failed_hint=False)
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_unreachable("web1", "u1", msg="connection refused\nretry later"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        unreachable_lines = [line for line in logged if "UNREACHABLE!" in line]
        assert unreachable_lines
        assert all(" => " not in line for line in unreachable_lines)


class TestHideUnreachable:
    def test_unreachable_lines_are_suppressed(self):
        r = _renderer(hide_states=["unreachable"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_unreachable("web1", "u1", msg="Connection refused"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("UNREACHABLE" in line for line in logged)


class TestHideMultiple:
    def test_ok_and_skipped_both_suppressed(self):
        r = _renderer(hide_states=["ok", "skipped"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [web1]" in line for line in logged)
        assert not any("skipping" in line for line in logged)

    def test_failed_and_ok_both_suppressed(self):
        r = _renderer(hide_states=["failed", "ok"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_failed("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [web1]" in line for line in logged)
        assert not any("FAILED" in line for line in logged)


class TestHideStateDefaults:
    def test_no_hide_states_prints_all_lines(self):
        r = _renderer()
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_skipped("web2", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("ok: [web1]" in line for line in logged)
        assert any("skipping: [web2]" in line for line in logged)

    def test_empty_hide_states_prints_all_lines(self):
        r = _renderer(hide_states=[])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("ok: [web1]" in line for line in logged)


class TestHideStateRunStateUnaffected:
    def test_ok_hidden_still_updates_state(self):
        r = _renderer(hide_states=["ok"])
        r._state = RunState(playbook="test.yml")
        r._state.handle_event(_play_start("Deploy"))
        r._emit_event_log(_task_start("T", "u1"))
        r._state.handle_event(_task_start("T", "u1"))
        r._emit_event_log(_ok("web1", "u1"))
        r._state.handle_event(_ok("web1", "u1"))
        hosts: set[str] = set()
        for play in r._state.plays.values():
            for task in play.tasks.values():
                hosts.update(task.hosts.keys())
        assert "web1" in hosts

    def test_skipped_hidden_still_updates_state(self):
        r = _renderer(hide_states=["skipped"])
        r._state = RunState(playbook="test.yml")
        r._state.handle_event(_play_start("Deploy"))
        r._emit_event_log(_task_start("T", "u1"))
        r._state.handle_event(_task_start("T", "u1"))
        r._emit_event_log(_skipped("web1", "u1"))
        r._state.handle_event(_skipped("web1", "u1"))
        hosts: set[str] = set()
        for play in r._state.plays.values():
            for task in play.tasks.values():
                hosts.update(task.hosts.keys())
        assert "web1" in hosts

    def test_failed_hidden_still_updates_state(self):
        r = _renderer(hide_states=["failed"])
        r._state = RunState(playbook="test.yml")
        r._state.handle_event(_play_start("Deploy"))
        r._emit_event_log(_task_start("T", "u1"))
        r._state.handle_event(_task_start("T", "u1"))
        r._emit_event_log(_failed("web1", "u1"))
        r._state.handle_event(_failed("web1", "u1"))
        hosts: set[str] = set()
        for play in r._state.plays.values():
            for task in play.tasks.values():
                hosts.update(task.hosts.keys())
        assert "web1" in hosts

    def test_unreachable_hidden_still_updates_state(self):
        r = _renderer(hide_states=["unreachable"])
        r._state = RunState(playbook="test.yml")
        r._state.handle_event(_play_start("Deploy"))
        r._emit_event_log(_task_start("T", "u1"))
        r._state.handle_event(_task_start("T", "u1"))
        r._emit_event_log(_unreachable("web1", "u1"))
        r._state.handle_event(_unreachable("web1", "u1"))
        hosts: set[str] = set()
        for play in r._state.plays.values():
            for task in play.tasks.values():
                hosts.update(task.hosts.keys())
        assert "web1" in hosts


def _multi_host_ok(uuid: str = "u1", ts: str = "2026-05-11T10:00:01Z") -> dict:
    """Event with web1=ok (changed=False) and web2=changed (changed=True)."""
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {"web1": {"changed": False}, "web2": {"changed": True}},
    }


class TestHideOkPerHost:
    """Per-host granularity: --hide-state ok suppresses ONLY ok: lines,
    not changed: lines, even when both hosts arrive in the same event."""

    def test_only_ok_suppressed_in_multi_host_event(self):
        r = _renderer(hide_states=["ok"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_multi_host_ok("u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [web1]" in line for line in logged), (
            f"'ok:' line for web1 should be hidden, got: {logged}"
        )
        assert any("changed: [web2]" in line for line in logged), (
            f"'changed:' line for web2 should print, got: {logged}"
        )

    def test_hide_ok_and_changed_suppresses_both(self):
        r = _renderer(hide_states=["ok", "changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_multi_host_ok("u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [web1]" in line for line in logged)
        assert not any("changed: [web2]" in line for line in logged)


class TestHideChangedPerHost:
    """Per-host granularity: --hide-state changed suppresses ONLY changed:
    lines, not ok: lines, even when both hosts arrive in the same event."""

    def test_only_changed_suppressed_in_multi_host_event(self):
        r = _renderer(hide_states=["changed"])
        r._emit_event_log(_task_start("T", "u1"))
        r._emit_event_log(_multi_host_ok("u1"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("changed: [web2]" in line for line in logged), (
            f"'changed:' line for web2 should be hidden, got: {logged}"
        )
        assert any("ok: [web1]" in line for line in logged), (
            f"'ok:' line for web1 should print, got: {logged}"
        )


def _aom_jsonl_item_event(
    event: str,
    host: str,
    label: str,
    *,
    changed: bool = False,
    msg: str | None = None,
    uuid: str = "u1",
    ts: str = "2026-05-11T10:00:01Z",
) -> dict:
    """Build a per-item event matching the real aom_jsonl callback payload shape.

    The real callback does NOT set ``failed``/``skipped`` flags on per-item
    payloads — those flags only appear on the aggregate host result. This
    helper omits them so tests match production behaviour.
    """
    raw: dict = {"_ansible_item_label": label, "item": label, "changed": changed}
    if msg is not None:
        raw["msg"] = msg
    return {
        "_event": event,
        "_timestamp": ts,
        "task": {"id": uuid},
        "hosts": {host: raw},
    }


class TestHideStatePreservesFailedItemMessage:
    """When --hide-state ok,skipped hides ok/skipped items, the failed item
    from a loop must still render as 'failed:' with its msg — not silently
    dropped or rendered as 'ok:'.

    The real aom_jsonl callback emits v2_runner_item_on_failed WITHOUT a
    ``failed: True`` flag in the per-item payload, so the renderer must use
    the event type to determine the display state.
    """

    def test_failed_item_visible_with_hide_state_ok_skipped(self):
        r = _renderer(hide_states=["ok", "skipped"])
        r._emit_event_log(_task_start("Copy files", "u1"))
        r._emit_event_log(
            _aom_jsonl_item_event(
                "v2_runner_item_on_failed",
                "localhost",
                "/opt/firefly/missing",
                msg="Destination directory /opt/firefly/missing does not exist",
            )
        )
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        failed_lines = [line for line in logged if "failed:" in line]
        assert len(failed_lines) >= 1, f"Expected at least one 'failed:' line, got: {logged}"
        assert any("item=/opt/firefly/missing" in line for line in logged), (
            f"Expected item label in output, got: {logged}"
        )
        assert any("does not exist" in line for line in logged), (
            f"Expected error msg in output, got: {logged}"
        )

    def test_ok_item_hidden_with_hide_state_ok_skipped(self):
        r = _renderer(hide_states=["ok", "skipped"])
        r._emit_event_log(_task_start("Copy files", "u1"))
        r._emit_event_log(_aom_jsonl_item_event("v2_runner_item_on_ok", "localhost", "apple"))
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("ok: [localhost]" in line for line in logged), (
            f"ok: line should be hidden, got: {logged}"
        )

    def test_changed_item_visible_with_hide_state_ok_skipped(self):
        r = _renderer(hide_states=["ok", "skipped"])
        r._emit_event_log(_task_start("Copy files", "u1"))
        r._emit_event_log(
            _aom_jsonl_item_event("v2_runner_item_on_ok", "localhost", "banana", changed=True)
        )
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert any("changed: [localhost]" in line for line in logged), (
            f"changed: line should print, got: {logged}"
        )

    def test_skipped_item_hidden_with_hide_state_ok_skipped(self):
        r = _renderer(hide_states=["ok", "skipped"])
        r._emit_event_log(_task_start("Copy files", "u1"))
        r._emit_event_log(
            _aom_jsonl_item_event("v2_runner_item_on_skipped", "localhost", "skip_me")
        )
        r._emit_event_log(_task_start("Next", "u2"))
        logged = _logged(r)
        assert not any("skipping: [localhost]" in line for line in logged), (
            f"skipping: line should be hidden, got: {logged}"
        )
