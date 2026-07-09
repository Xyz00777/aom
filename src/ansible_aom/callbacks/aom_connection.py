"""AOM connection-tracking callback plugin.

Emits ``aom_connection_acquired`` and ``aom_connection_released`` JSONL
events to a log file (``AOM_CONNECTION_LOG`` env var) so AOM can track
per-host connection state across a playbook run.

This is a notification-type callback (not stdout). It is loaded via
``ANSIBLE_CALLBACK_PLUGINS`` alongside the stdout callback and runs
inside the ansible-playbook subprocess.

Event shape (JSONL, one object per line):

.. code-block:: json

    {"_event": "aom_connection_acquired", "connection_id": "<uuid>",
     "task_uuid": "<uuid>", "host": "web1", "_timestamp": "2026-07-01T12:00:00Z"}
    {"_event": "aom_connection_released", "connection_id": "<uuid>",
     "task_uuid": "<uuid>", "host": "web1", "_timestamp": "2026-07-01T12:00:01Z"}

``connection_id`` is a stable UUID per (task_uuid, host) pair so AOM can
match acquire/release pairs. ``task_uuid`` is the ansible task UUID from
the runner callback. ``host`` is the target hostname.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = """
    name: aom_connection
    type: notification
    short_description: Emit connection acquire/release events for AOM
    description:
      - Emits aom_connection_acquired on v2_runner_on_start and
        aom_connection_released on v2_runner_on_ok/failed/unreachable/skipped.
      - Events are written as JSONL to the file specified by AOM_CONNECTION_LOG.
      - connection_id is a deterministic UUID per (task_uuid, host) pair.
    requirements:
      - Set AOM_CONNECTION_LOG environment variable to a writable file path.
"""


def _connection_id(task_uuid: str, host: str) -> str:
    """Return a deterministic UUID for a (task_uuid, host) pair."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{task_uuid}/{host}"))


def _timestamp() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _make_acquired(task_uuid: str, host: str) -> dict[str, object]:
    """Build an ``aom_connection_acquired`` event dict."""
    return {
        "_event": "aom_connection_acquired",
        "connection_id": _connection_id(task_uuid, host),
        "task_uuid": task_uuid,
        "host": host,
        "_timestamp": _timestamp(),
    }


def _make_released(task_uuid: str, host: str) -> dict[str, object]:
    """Build an ``aom_connection_released`` event dict."""
    return {
        "_event": "aom_connection_released",
        "connection_id": _connection_id(task_uuid, host),
        "task_uuid": task_uuid,
        "host": host,
        "_timestamp": _timestamp(),
    }


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "aom_connection"
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self) -> None:
        super().__init__()
        self._log_path: str | None = os.environ.get("AOM_CONNECTION_LOG")

    def _write_event(self, event: dict[str, object]) -> None:
        if self._log_path is None:
            return
        try:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(event, sort_keys=True) + "\n")
        except OSError:
            pass

    def v2_runner_on_start(self, result) -> None:
        host = result._host.get_name()
        task_uuid = result._task._uuid
        self._write_event(_make_acquired(task_uuid, host))

    def v2_runner_on_ok(self, result) -> None:
        host = result._host.get_name()
        task_uuid = result._task._uuid
        self._write_event(_make_released(task_uuid, host))

    def v2_runner_on_failed(self, result, ignore_errors=False) -> None:
        host = result._host.get_name()
        task_uuid = result._task._uuid
        self._write_event(_make_released(task_uuid, host))

    def v2_runner_on_unreachable(self, result) -> None:
        host = result._host.get_name()
        task_uuid = result._task._uuid
        self._write_event(_make_released(task_uuid, host))

    def v2_runner_on_skipped(self, result) -> None:
        host = result._host.get_name()
        task_uuid = result._task._uuid
        self._write_event(_make_released(task_uuid, host))
