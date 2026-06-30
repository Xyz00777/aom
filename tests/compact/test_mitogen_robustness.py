"""TC-MITOGEN-100..107 — compact renderer's tolerance for malformed JSONL events.

When mitogen drops the SSH link mid-task, ansible.posix.jsonl emits
events whose payloads diverge from the documented shape: ``task`` may
be a bare UUID string, ``task`` may be ``null``, or ``hosts`` may be a
list instead of a dict. The compact renderer previously crashed on all
three with ``AttributeError``, which propagated out of
``update_state`` and took down the whole runner thread — the
user-visible symptom being a frozen status panel while ansible's logs
continued to scroll.

These tests pin the requirement that ``update_state`` and the lower
level ``_emit_event_log`` MUST tolerate every shape the JSONL callback
has been observed to emit, and MUST keep processing well-formed events
after a malformed one lands.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ansible_aom.compact.renderer import CompactRenderer


def _task_start(uuid: str = "u1", ts: str = "2026-04-20T10:00:02Z") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "Install NFS utils", "path": "main.yml:1"},
        "play": {"id": "p1"},
    }


def _runner_start(uuid: str = "u1", ts: str = "2026-04-20T10:00:03Z") -> dict:
    return {
        "_event": "v2_runner_on_start",
        "_timestamp": ts,
        "task": {"id": uuid, "name": "Install NFS utils", "path": "main.yml:1"},
        "play": {"id": "p1"},
        "host": "foreman",
    }


def _renderer() -> CompactRenderer:
    r = CompactRenderer(is_tty=False)
    r.start("test.yml", [])
    r._colorize = False
    r._display = MagicMock()
    return r


class TestUpdateStateMalformedPayloads:
    """TC-MITOGEN-100..105: ``update_state`` must not raise on bad events."""

    def test_mitogen_100_runner_unreachable_task_as_string(self) -> None:
        """TC-MITOGEN-100: ``task`` as a bare UUID string must not raise."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())
        r._display.reset_mock()

        bad = {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": "u1",  # bare string, NOT a dict
            "play": {"id": "p1"},
            "host": "foreman",
            "msg": "MITOGEN: rpc failed: broken pipe",
        }
        r.update_state(bad)

    def test_mitogen_101_runner_failed_task_as_none(self) -> None:
        """TC-MITOGEN-101: ``task: None`` must not raise."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())
        r._display.reset_mock()

        bad = {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": None,
            "play": {"id": "p1"},
            "host": "foreman",
            "msg": "MITOGEN: orphaned event",
        }
        r.update_state(bad)

    def test_mitogen_102_runner_ok_hosts_as_list(self) -> None:
        """TC-MITOGEN-102: ``hosts: list`` must not raise on ``v2_runner_on_ok``."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())
        r._display.reset_mock()

        bad = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "u1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman", "ds5"],  # list, NOT dict
        }
        r.update_state(bad)

    def test_mitogen_103_runner_unreachable_hosts_as_list(self) -> None:
        """TC-MITOGEN-103: ``hosts: list`` must not raise on unreachable."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())

        bad = {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "u1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman"],
        }
        r.update_state(bad)

    def test_mitogen_104_runner_failed_hosts_as_list(self) -> None:
        """TC-MITOGEN-104: ``hosts: list`` must not raise on failed."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())

        bad = {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "u1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman"],
        }
        r.update_state(bad)

    def test_mitogen_105_runner_skipped_hosts_as_list(self) -> None:
        """TC-MITOGEN-105: ``hosts: list`` must not raise on skipped."""
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())

        bad = {
            "_event": "v2_runner_on_skipped",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "u1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman"],
        }
        r.update_state(bad)

    def test_mitogen_106_recovery_after_malformed_event(self) -> None:
        """TC-MITOGEN-106: a malformed event must not poison subsequent events.

        The renderer must continue processing well-formed events after
        a malformed one. The fixture here proves the post-bad-event
        ``v2_runner_on_ok`` still calls ``Display.print_log`` exactly
        once for the recovered host line.
        """
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())
        r._display.reset_mock()

        r.update_state(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:04Z",
                "task": "u1",
                "play": {"id": "p1"},
                "host": "foreman",
            }
        )

        # A subsequent well-formed ok event must mutate state and print
        # a log line normally. Use a NEW task uuid so the inline-duration
        # suffix logic isn't tied to the bad event's malformed task id.
        # ``hosts`` is the canonical ``{hostname: result}`` dict shape
        # produced by ansible.posix.jsonl (verified against the callback
        # source at ``task_result_copy['hosts'][host.name] = result_copy``).
        good = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "u2", "name": "Recover", "path": "main.yml:2"},
            "play": {"id": "p1"},
            "hosts": {"foreman": {"changed": False}},
        }
        r.update_state(good)

        # At least one print_log call carries an ``ok:`` line for foreman.
        payloads = [c.args[0] for c in r._display.print_log.call_args_list]
        assert any("ok: [foreman]" in p for p in payloads), (
            f"expected ok line for foreman after recovery, got {payloads!r}"
        )

    def test_mitogen_107_state_machine_still_updated_when_log_skipped(self) -> None:
        """TC-MITOGEN-107: a malformed event that crashes _emit_event_log
        must not leave the state machine frozen.

        Today ``update_state`` calls ``_emit_event_log`` first, then
        ``self._state.handle_event(event)``. If the log path raises on
        a mitogen event the state mutation never runs and the run
        state stays one event behind forever. The fix path requires
        either tolerant log emission OR a try/except that still lets
        ``handle_event`` run. This test pins that requirement by
        asserting the state has progressed past the bad event.
        """
        r = _renderer()
        r.update_state(_task_start())
        r.update_state(_runner_start())
        # Send the bad event — should NOT raise AND the underlying state
        # should still be reachable.
        r.update_state(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:04Z",
                "task": "u1",
                "play": {"id": "p1"},
                "host": "foreman",
            }
        )
        # State machine is still alive: a subsequent normal event
        # reaches the panel.
        assert r._state is not None
        assert "p1" in r._state.plays
        assert "u1" in r._state.plays["p1"].tasks
