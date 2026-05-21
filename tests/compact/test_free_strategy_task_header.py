"""Under the free strategy ``ansible.posix.jsonl`` does not always emit
``v2_playbook_on_task_start`` before runner events fire — instead
``v2_runner_on_start`` arrives per host as each host begins the task.

Without seeing the TASK header in the log the user has no idea which
task the streaming ``ok: [host]`` lines belong to. Emit the header on
the first ``v2_runner_on_start`` for a previously-unannounced task too.
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


def _runner_start(task_id: str, task_name: str, host: str) -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": "2026-05-22T10:00:01Z",
        "task": {"id": task_id, "name": task_name},
        "host": host,
    }


def _runner_ok(task_id: str, host: str) -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": "2026-05-22T10:00:02Z",
        "task": {"id": task_id},
        "hosts": {host: {"changed": False}},
    }


def test_task_header_emitted_on_first_runner_start_when_no_task_start() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Install nginx", "web1"))
    printed = _printed(r)
    assert any("TASK [Install nginx]" in line for line in printed), printed


def test_task_header_not_repeated_on_subsequent_runner_starts() -> None:
    """Each host fires runner_start; the header must print only once."""
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "Install nginx", "web1"))
    r._emit_event_log(_runner_start("t1", "Install nginx", "web2"))
    r._emit_event_log(_runner_start("t1", "Install nginx", "web3"))
    printed = _printed(r)
    headers = [line for line in printed if "TASK [Install nginx]" in line]
    assert len(headers) == 1, headers


def test_task_header_not_duplicated_when_task_start_already_fired() -> None:
    """Linear strategy fires task_start; free fires runner_start. A run
    that emits both for the same task (some plays may overlap) still
    prints exactly one TASK header."""
    r = _renderer()
    r._emit_event_log(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-05-22T10:00:00Z",
            "task": {"id": "t1", "name": "Install nginx"},
            "play": {"id": "p1"},
        }
    )
    r._emit_event_log(_runner_start("t1", "Install nginx", "web1"))
    printed = _printed(r)
    headers = [line for line in printed if "TASK [Install nginx]" in line]
    assert len(headers) == 1, headers


def test_new_task_after_first_gets_its_own_header() -> None:
    r = _renderer()
    r._emit_event_log(_runner_start("t1", "first task", "web1"))
    r._emit_event_log(_runner_ok("t1", "web1"))
    r._emit_event_log(_runner_start("t2", "second task", "web1"))
    printed = _printed(r)
    assert any("TASK [first task]" in line for line in printed), printed
    assert any("TASK [second task]" in line for line in printed), printed
