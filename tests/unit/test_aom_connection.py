"""Tests for the AOM connection-tracking callback plugin.

Tests cover the pure helper functions (``_connection_id``, ``_timestamp``)
and the event construction methods (``_make_acquired``, ``_make_released``)
from ``ansible_aom.callbacks.aom_connection``. The full ``CallbackModule``
class requires ansible-core at runtime and is tested via integration tests.

Test cases:
- TC-connection-001: _connection_id is deterministic for same (task_uuid, host)
- TC-connection-002: _connection_id differs for different hosts
- TC-connection-003: _connection_id differs for different task_uuids
- TC-connection-004: _make_acquired produces correct event shape
- TC-connection-005: _make_released produces correct event shape
- TC-connection-006: acquire/release share same connection_id for same pair
- TC-connection-007: _timestamp returns ISO 8601 UTC string
- TC-connection-008: file writing via _write_event (with temp file)
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid

from ansible_aom.callbacks.aom_connection import (
    CallbackModule,
    _connection_id,
    _make_acquired,
    _make_released,
    _timestamp,
)


class TestConnectionId:
    def test_deterministic_for_same_pair(self) -> None:
        task_uuid = "abc-123"
        host = "web1"
        assert _connection_id(task_uuid, host) == _connection_id(task_uuid, host)

    def test_differs_for_different_hosts(self) -> None:
        task_uuid = "abc-123"
        assert _connection_id(task_uuid, "web1") != _connection_id(task_uuid, "web2")

    def test_differs_for_different_task_uuids(self) -> None:
        host = "web1"
        assert _connection_id("abc-123", host) != _connection_id("xyz-789", host)

    def test_returns_valid_uuid_string(self) -> None:
        cid = _connection_id("abc-123", "web1")
        parsed = uuid.UUID(cid)
        assert parsed.version == 5  # UUID5 (namespace DNS)


class TestEventConstruction:
    def test_acquired_event_shape(self) -> None:
        task_uuid = "task-001"
        host = "db1"
        event = _make_acquired(task_uuid, host)

        assert event["_event"] == "aom_connection_acquired"
        assert event["task_uuid"] == task_uuid
        assert event["host"] == host
        assert "connection_id" in event
        assert "_timestamp" in event
        assert event["connection_id"] == _connection_id(task_uuid, host)

    def test_released_event_shape(self) -> None:
        task_uuid = "task-001"
        host = "db1"
        event = _make_released(task_uuid, host)

        assert event["_event"] == "aom_connection_released"
        assert event["task_uuid"] == task_uuid
        assert event["host"] == host
        assert "connection_id" in event
        assert "_timestamp" in event
        assert event["connection_id"] == _connection_id(task_uuid, host)

    def test_acquire_release_share_connection_id(self) -> None:
        task_uuid = "task-002"
        host = "web3"
        acquired = _make_acquired(task_uuid, host)
        released = _make_released(task_uuid, host)
        assert acquired["connection_id"] == released["connection_id"]

    def test_timestamp_format(self) -> None:
        ts = _timestamp()
        assert ts.endswith("Z")
        assert "T" in ts
        # Should parse as ISO 8601
        from datetime import datetime

        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None


class TestFileWriting:
    def test_write_event_to_temp_file(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            log_path = f.name

        try:
            cb = CallbackModule()
            cb._log_path = log_path

            task_uuid = "task-write-001"
            host = "test-host"
            cb._write_event(_make_acquired(task_uuid, host))
            cb._write_event(_make_released(task_uuid, host))

            with open(log_path) as f:
                lines = f.readlines()

            assert len(lines) == 2
            event1 = json.loads(lines[0])
            event2 = json.loads(lines[1])

            assert event1["_event"] == "aom_connection_acquired"
            assert event2["_event"] == "aom_connection_released"
            assert event1["connection_id"] == event2["connection_id"]
            assert event1["host"] == host
            assert event2["host"] == host
        finally:
            try:
                os.unlink(log_path)
            except OSError:
                pass

    def test_write_event_noop_when_log_path_none(self) -> None:
        cb = CallbackModule()
        cb._log_path = None
        # Should not raise
        cb._write_event(_make_acquired("task-003", "host1"))


class TestRunnerOnStartSignature:
    """ansible-core dispatches ``v2_runner_on_start(host, task)`` — two
    positional args, unlike the result-carrying runner hooks. The wrong
    ``(self, result)`` signature made every dispatch fail with
    "[WARNING]: Callback dispatch 'v2_runner_on_start' failed", so
    connection tracking never recorded an acquire."""

    def test_v2_runner_on_start_accepts_host_and_task(self) -> None:
        class _Host:
            def get_name(self) -> str:
                return "web1"

        class _Task:
            _uuid = "task-start-001"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            log_path = f.name
        try:
            cb = CallbackModule()
            cb._log_path = log_path

            cb.v2_runner_on_start(_Host(), _Task())

            with open(log_path) as f:
                event = json.loads(f.readline())
            assert event["_event"] == "aom_connection_acquired"
            assert event["host"] == "web1"
        finally:
            try:
                os.unlink(log_path)
            except OSError:
                pass
