"""Straggler results print under the wrong TASK header.

Log lines stream in arrival order under the most recently announced
``TASK [...]`` header. Under throttle/free-strategy interleaving, a
result for task A can arrive after task B's header was already printed
— the line then visually reads as an A-result for B. Flag those lines
with a ``[task: <name>]`` suffix so the misattribution is visible.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ansible_aom.compact.renderer import CompactRenderer


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


def _printed(r: CompactRenderer) -> list[str]:
    return [c.args[0] for c in r._display.print_log.call_args_list]


def _runner_start(task_id: str, task_name: str, host: str, ts: str) -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": ts,
        "task": {"id": task_id, "name": task_name},
        "host": host,
    }


def _runner_ok(task_id: str, task_name: str, host: str, ts: str) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": task_id, "name": task_name},
        "hosts": {host: {"changed": False}},
    }


def _runner_failed(task_id: str, task_name: str, host: str, ts: str) -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": ts,
        "task": {"id": task_id, "name": task_name},
        "hosts": {host: {"failed": True, "msg": "boom"}},
    }


def test_straggler_ok_line_carries_task_suffix() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Check db exists", "web1", "2026-05-22T10:00:00Z"))
    r._emit_event_log(_runner_start("t2", "Update db", "web2", "2026-05-22T10:00:01Z"))
    # web1's result for t1 arrives after t2's header was printed.
    r._emit_event_log(_runner_ok("t1", "Check db exists", "web1", "2026-05-22T10:00:02Z"))
    printed = _printed(r)
    ok_lines = [line for line in printed if "ok: [web1]" in line]
    assert len(ok_lines) == 1, printed
    assert "[task: Check db exists]" in ok_lines[0]


def test_result_matching_current_header_has_no_task_suffix() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Check db exists", "web1", "2026-05-22T10:00:00Z"))
    r._emit_event_log(_runner_ok("t1", "Check db exists", "web1", "2026-05-22T10:00:02Z"))
    printed = _printed(r)
    ok_lines = [line for line in printed if "ok: [web1]" in line]
    assert len(ok_lines) == 1, printed
    assert "[task:" not in ok_lines[0]


def test_straggler_failed_line_carries_task_suffix() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Check db exists", "web1", "2026-05-22T10:00:00Z"))
    r._emit_event_log(_runner_start("t2", "Update db", "web2", "2026-05-22T10:00:01Z"))
    r._emit_event_log(_runner_failed("t1", "Check db exists", "web1", "2026-05-22T10:00:02Z"))
    printed = _printed(r)
    fatal_lines = [line for line in printed if "fatal: [web1]" in line]
    assert len(fatal_lines) == 1, printed
    assert "[task: Check db exists]" in fatal_lines[0]


def test_straggler_changed_line_carries_task_suffix() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Check db exists", "web1", "2026-05-22T10:00:00Z"))
    r._emit_event_log(_runner_start("t2", "Update db", "web2", "2026-05-22T10:00:01Z"))
    event = _runner_ok("t1", "Check db exists", "web1", "2026-05-22T10:00:02Z")
    event["hosts"]["web1"]["changed"] = True
    r._emit_event_log(event)
    printed = _printed(r)
    changed_lines = [line for line in printed if "changed: [web1]" in line]
    assert len(changed_lines) == 1, printed
    assert "[task: Check db exists]" in changed_lines[0]
