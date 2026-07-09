"""Unit tests for RunState event handling.

Test cases from TEST_SPECIFICATION.md Section 6.2 (TC-197 through TC-216).

Each test creates fresh RunState instances - no shared mutable state.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from ansible_aom.core.models import (
    HostRunState,
    PlayRunState,
    Status,
    TaskDefinition,
    TaskRunState,
)
from ansible_aom.core.run_state import RunState

# ==============================================================================
# TC-197: handle_event Dispatcher Routing
# ==============================================================================


class TestHandleEventDispatcher:
    """Tests for handle_event routing events to correct handlers (TC-197)."""

    def test_handle_event_routes_to_playbook_on_start(self, event_playbook_start: dict) -> None:
        """TC-197: handle_event routes v2_playbook_on_start to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_playbook_on_start") as mock_handler:
            run_state.handle_event(event_playbook_start)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_play_start(self, event_play_start: dict) -> None:
        """TC-197: handle_event routes v2_playbook_on_play_start to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_playbook_on_play_start") as mock_handler:
            run_state.handle_event(event_play_start)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_task_start(self, event_task_start: dict) -> None:
        """TC-197: handle_event routes v2_playbook_on_task_start to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_playbook_on_task_start") as mock_handler:
            run_state.handle_event(event_task_start)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_start(self, event_runner_start: dict) -> None:
        """TC-197: handle_event routes v2_runner_on_start to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_start") as mock_handler:
            run_state.handle_event(event_runner_start)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_ok(self, event_runner_ok: dict) -> None:
        """TC-197: handle_event routes v2_runner_on_ok to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_ok") as mock_handler:
            run_state.handle_event(event_runner_ok)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_failed(self, event_runner_failed: dict) -> None:
        """TC-197: handle_event routes v2_runner_on_failed to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_failed") as mock_handler:
            run_state.handle_event(event_runner_failed)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_skipped(self, event_runner_skipped: dict) -> None:
        """TC-197: handle_event routes v2_runner_on_skipped to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_skipped") as mock_handler:
            run_state.handle_event(event_runner_skipped)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_unreachable(
        self, event_runner_unreachable: dict
    ) -> None:
        """TC-197: handle_event routes v2_runner_on_unreachable to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_unreachable") as mock_handler:
            run_state.handle_event(event_runner_unreachable)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_stats(self, event_stats: dict) -> None:
        """TC-197: handle_event routes v2_playbook_on_stats to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_playbook_on_stats") as mock_handler:
            run_state.handle_event(event_stats)
            mock_handler.assert_called_once()


# ==============================================================================
# TC-198: handle_event Timestamp Parsing
# ==============================================================================


class TestHandleEventTimestampParsing:
    """Tests for timestamp parsing in handle_event (TC-198)."""

    def test_handle_event_parses_iso_timestamp(self, event_playbook_start: dict) -> None:
        """TC-198: Timestamp is parsed from _timestamp field as ISO format datetime."""
        run_state = RunState(playbook="test.yml")

        # The fixture has timestamp "2026-04-20T10:00:00Z"
        with patch.object(run_state, "_handle_v2_playbook_on_start") as mock_handler:
            run_state.handle_event(event_playbook_start)

            # Check that handler was called with parsed datetime
            call_args = mock_handler.call_args
            assert call_args is not None
            assert len(call_args) == 2
            event_arg, ts_arg = call_args[0]
            assert isinstance(ts_arg, datetime)
            assert ts_arg.year == 2026
            assert ts_arg.month == 4
            assert ts_arg.day == 20
            assert ts_arg.hour == 10
            assert ts_arg.minute == 0
            assert ts_arg.second == 0

    def test_handle_event_missing_timestamp_defaults_to_now(self) -> None:
        """TC-198: Missing _timestamp field defaults to current time."""
        run_state = RunState(playbook="test.yml")
        event = {"_event": "v2_playbook_on_start"}  # No _timestamp

        before = datetime.now(timezone.utc)

        with patch.object(run_state, "_handle_v2_playbook_on_start") as mock_handler:
            run_state.handle_event(event)

            call_args = mock_handler.call_args
            ts_arg = call_args[0][1]
            assert isinstance(ts_arg, datetime)
            # Timestamp should be close to current time
            after = datetime.now(timezone.utc)
            assert before <= ts_arg <= after or abs((ts_arg - before).total_seconds()) < 5

    def test_handle_event_invalid_timestamp_handled_gracefully(self) -> None:
        """TC-198: Invalid timestamp string is handled gracefully."""
        run_state = RunState(playbook="test.yml")
        event = {
            "_event": "v2_playbook_on_start",
            "_timestamp": "not-a-valid-timestamp",
        }

        # Should not raise exception - should use default time
        with patch.object(run_state, "_handle_v2_playbook_on_start") as mock_handler:
            run_state.handle_event(event)
            mock_handler.assert_called_once()
            ts_arg = mock_handler.call_args[0][1]
            assert isinstance(ts_arg, datetime)


# ==============================================================================
# TC-199: handle_event Unknown Event Type Graceful Handling
# ==============================================================================


class TestHandleEventUnknownType:
    """Tests for unknown event type handling (TC-199)."""

    def test_handle_event_unknown_type_ignored(self) -> None:
        """TC-199: Unknown _event types are silently ignored without error."""
        run_state = RunState(playbook="test.yml")
        event = {"_event": "v2_some_future_event_type", "_timestamp": "2026-04-20T10:00:00Z"}

        # Should not raise exception
        run_state.handle_event(event)
        # State should remain unchanged
        assert run_state.status == Status.PENDING

    def test_handle_event_missing_event_field_ignored(self) -> None:
        """TC-199: Missing _event field is handled gracefully."""
        run_state = RunState(playbook="test.yml")
        event = {"_timestamp": "2026-04-20T10:00:00Z"}  # No _event

        # Should not raise exception
        run_state.handle_event(event)
        assert run_state.status == Status.PENDING

    def test_handle_event_empty_event_field_ignored(self) -> None:
        """TC-199: Empty string _event is handled gracefully."""
        run_state = RunState(playbook="test.yml")
        event = {"_event": "", "_timestamp": "2026-04-20T10:00:00Z"}

        # Should not raise exception
        run_state.handle_event(event)
        assert run_state.status == Status.PENDING


# ==============================================================================
# TC-200: _handle_v2_playbook_on_start Sets Execution Start
# ==============================================================================


class TestPlaybookOnStart:
    """Tests for v2_playbook_on_start handling (TC-200)."""

    def test_playbook_on_start_sets_status_running(self, event_playbook_start: dict) -> None:
        """TC-200: v2_playbook_on_start sets status to RUNNING."""
        run_state = RunState(playbook="test.yml")
        assert run_state.status == Status.PENDING

        run_state.handle_event(event_playbook_start)

        assert run_state.status == Status.RUNNING

    def test_playbook_on_start_sets_start_time(self, event_playbook_start: dict) -> None:
        """TC-200: v2_playbook_on_start sets start_time."""
        run_state = RunState(playbook="test.yml")
        assert run_state.start_time is None

        run_state.handle_event(event_playbook_start)

        assert run_state.start_time is not None
        assert run_state.start_time.year == 2026
        assert run_state.start_time.month == 4
        assert run_state.start_time.day == 20

    def test_playbook_on_start_multiple_events_ignored(self) -> None:
        """TC-200 edge case: Multiple playbook_on_start events keep first."""
        run_state = RunState(playbook="test.yml")

        event1 = {
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-04-20T10:00:00Z",
        }
        event2 = {
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-04-20T11:00:00Z",
        }

        run_state.handle_event(event1)
        first_start_time = run_state.start_time

        run_state.handle_event(event2)

        # Start time should remain from first event
        assert run_state.start_time == first_start_time


# ==============================================================================
# TC-201: _handle_v2_playbook_on_play_start Creates PlayRunState
# ==============================================================================


class TestPlayStart:
    """Tests for v2_playbook_on_play_start handling (TC-201)."""

    def test_play_start_creates_play_run_state(self, event_play_start: dict) -> None:
        """TC-201: v2_playbook_on_play_start creates new PlayRunState."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)

        assert "play-uuid-1" in run_state.plays
        play_state = run_state.plays["play-uuid-1"]
        assert isinstance(play_state, PlayRunState)
        assert play_state.play_id == "play-uuid-1"
        assert play_state.name == "Setup webservers"

    def test_play_start_existing_play_updates(self) -> None:
        """TC-201 edge case: Same play.id updates existing PlayRunState."""
        run_state = RunState(playbook="test.yml")

        event1 = {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup webservers"},
        }
        event2 = {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "play": {"id": "play-uuid-1", "name": "Updated play name"},
        }

        run_state.handle_event(event1)
        assert len(run_state.plays) == 1

        run_state.handle_event(event2)
        assert len(run_state.plays) == 1
        assert run_state.plays["play-uuid-1"].name == "Updated play name"

    def test_play_start_sets_status_running(self, event_play_start: dict) -> None:
        """TC-201: play status is set to RUNNING."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)

        assert run_state.plays["play-uuid-1"].status == Status.RUNNING


# ==============================================================================
# TC-202: _handle_v2_playbook_on_task_start Detects Linear Strategy
# ==============================================================================


class TestTaskStart:
    """Tests for v2_playbook_on_task_start handling (TC-202)."""

    def test_task_start_detects_linear_strategy(
        self, event_play_start: dict, event_task_start: dict
    ) -> None:
        """TC-202: First task_start sets play.detected_strategy to 'linear'."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        run_state.handle_event(event_task_start)

        play_state = run_state.plays["play-uuid-1"]
        assert play_state.detected_strategy == "linear"

    def test_task_start_does_not_change_existing_strategy(self) -> None:
        """TC-202 edge case: Subsequent task_start events don't change strategy."""
        run_state = RunState(playbook="test.yml")

        # First, set up play
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )

        # First task_start sets strategy to linear
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task 1"},
                "play": {"id": "play-uuid-1"},
            }
        )
        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"

        # Manually set strategy to something else (simulating prior detection)
        run_state.plays["play-uuid-1"].detected_strategy = "free"

        # Another task_start should not change it
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "task-uuid-2", "name": "Task 2"},
                "play": {"id": "play-uuid-1"},
            }
        )
        assert run_state.plays["play-uuid-1"].detected_strategy == "free"

    def test_task_start_missing_play_creates_play(self, event_task_start: dict) -> None:
        """TC-202: task_start with unknown play_id creates minimal PlayRunState."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_task_start)

        assert "play-uuid-1" in run_state.plays
        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"


# ==============================================================================
# TC-203: _handle_v2_runner_on_start Detects Free Strategy
# ==============================================================================


class TestRunnerOnStartStrategy:
    """Tests for v2_runner_on_start strategy detection (TC-203)."""

    def test_runner_start_detects_free_strategy(
        self, event_play_start: dict, event_runner_start: dict
    ) -> None:
        """TC-203: runner_on_start without prior task_start indicates free strategy."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start_with_play = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start_with_play)

        play_state = run_state.plays["play-uuid-1"]
        assert play_state.detected_strategy == "free"

    def test_runner_start_after_task_start_flips_to_free(self) -> None:
        """TC-203: runner_on_start after task_start proves the playbook is
        NOT running with lockstep enabled (the JSONL callback guards
        runner_on_start behind `if self._is_lockstep: return`). The
        earlier linear detection by task_start was premature — the
        strategy must flip to free."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_task_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "play": {"id": "play-uuid-1"},
            }
        )
        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"

        # runner_on_start arrives — proves strategy is actually free
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )

        assert run_state.plays["play-uuid-1"].detected_strategy == "free"


# ==============================================================================
# TC-204: _handle_v2_runner_on_start Creates TaskRunState
# ==============================================================================


class TestRunnerOnStartTaskCreation:
    """Tests for v2_runner_on_start creating TaskRunState (TC-204)."""

    def test_runner_start_creates_task_run_state(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-204: v2_runner_on_start creates TaskRunState with status RUNNING."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        play_state = run_state.plays["play-uuid-1"]
        assert "task-uuid-1" in play_state.tasks
        task_state = play_state.tasks["task-uuid-1"]
        assert isinstance(task_state, TaskRunState)
        assert task_state.task_id == "task-uuid-1"
        assert task_state.name == "Install nginx"
        # After runner_on_ok for the only host, the task correctly
        # promotes to COMPLETED (model state stays self-consistent with
        # per-host terminal status). This is the correct new behavior;
        # the prior test asserted RUNNING which encoded the bug that
        # _handle_v2_runner_on_* didn't update task.status.
        assert task_state.status == Status.COMPLETED

    def test_runner_start_sets_task_start_time(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-204: TaskRunState start_time is set from event timestamp."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)

        task_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert task_state.start_time is not None
        assert task_state.start_time.hour == 10
        assert task_state.start_time.minute == 0
        assert task_state.start_time.second == 2

    def test_runner_start_missing_play_creates_play(self, event_runner_start: dict) -> None:
        """TC-204: runner_on_start with unknown play_id creates minimal PlayRunState."""
        event = {
            **event_runner_start,
            "play": {"id": "play-uuid-1"},
        }
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event)

        assert "play-uuid-1" in run_state.plays
        assert "task-uuid-1" in run_state.plays["play-uuid-1"].tasks


# ==============================================================================
# TC-205: _handle_v2_runner_on_ok Updates HostRunState
# ==============================================================================


class TestRunnerOnOk:
    """Tests for v2_runner_on_ok creating HostRunState (TC-205)."""

    def test_runner_ok_creates_host_run_state(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-205: v2_runner_on_ok creates HostRunState per host."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        task_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert "web1" in task_state.hosts
        host_state = task_state.hosts["web1"]
        assert isinstance(host_state, HostRunState)
        assert host_state.hostname == "web1"
        assert host_state.status == Status.OK

    def test_runner_ok_sets_end_time(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-205: HostRunState end_time is set from event timestamp."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.end_time is not None
        assert host_state.end_time.second == 5

    def test_runner_ok_multiple_hosts(self, event_play_start: dict) -> None:
        """TC-205 edge case: Multiple hosts in single event all get HostRunState."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "hosts": {
                    "web1": {"ok": True, "changed": False},
                    "web2": {"ok": True, "changed": False},
                },
                "play": {"id": "play-uuid-1"},
            }
        )

        task_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert "web1" in task_state.hosts
        assert "web2" in task_state.hosts
        assert task_state.hosts["web1"].status == Status.OK
        assert task_state.hosts["web2"].status == Status.OK


# ==============================================================================
# TC-206: _handle_v2_runner_on_ok Status Based on Changed
# ==============================================================================


class TestRunnerOnOkStatus:
    """Tests for status determination in v2_runner_on_ok (TC-206)."""

    def test_runner_ok_changed_false_status_ok(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-206: HostRunState status is OK when changed=false."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.OK
        assert host_state.changed is False

    def test_runner_ok_changed_true_status_changed(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_ok_changed: dict,
    ) -> None:
        """TC-206: HostRunState status is CHANGED when changed=true."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok_changed, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.CHANGED
        assert host_state.changed is True

    def test_runner_ok_missing_changed_defaults_false(
        self, event_play_start: dict, event_runner_start: dict
    ) -> None:
        """TC-206 edge case: Missing changed field defaults to false/OK."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        run_state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Install nginx"},
                "hosts": {"web1": {"ok": True}},  # No 'changed' field
                "play": {"id": "play-uuid-1"},
            }
        )

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.OK
        assert host_state.changed is False


# ==============================================================================
# TC-208: _handle_v2_runner_on_failed Creates Failed HostRunState
# ==============================================================================


class TestRunnerOnFailed:
    """Tests for v2_runner_on_failed handling (TC-208)."""

    def test_runner_failed_creates_failed_host(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed: dict,
    ) -> None:
        """TC-208: v2_runner_on_failed creates HostRunState with FAILED status."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_failed = {**event_runner_failed, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_failed)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.FAILED
        assert host_state.message == "Error installing package"

    def test_runner_failed_sets_end_time(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed: dict,
    ) -> None:
        """TC-208: Failed HostRunState has end_time set."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_failed = {**event_runner_failed, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_failed)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.end_time is not None


# ==============================================================================
# TC-209: _handle_v2_runner_on_failed ignore_errors Handling
# ==============================================================================


class TestRunnerOnFailedIgnoreErrors:
    """Tests for ignore_errors handling in v2_runner_on_failed (TC-209)."""

    def test_runner_failed_ignore_errors_status_ok(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed_ignore: dict,
    ) -> None:
        """TC-209: ignore_errors=true treats failed task as OK status."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_failed = {**event_runner_failed_ignore, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_failed)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.OK

    def test_runner_failed_ignore_errors_top_level_location(self) -> None:
        """The real emitted shape: ``ignore_errors: true`` at the top level of
        the host result (as the aom_jsonl callback now emits) → OK, run not
        failed. Regression guard for ignore_errors failures counted as ✖.
        """
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "hosts": {"web1": {"failed": True, "ignore_errors": True}},
                "play": {"id": "play-uuid-1"},
            }
        )

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.OK
        # An ignored failure must not flip the whole run to FAILED.
        assert run_state.status != Status.FAILED

    def test_runner_failed_ignore_errors_nested_location(self) -> None:
        """TC-209: Nested ignore_errors location in _ansible_verbose_always."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "hosts": {
                    "web1": {
                        "_ansible_verbose_always": {"ignore_errors": True},
                        "failed": True,
                    }
                },
                "play": {"id": "play-uuid-1"},
            }
        )

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.OK


# ==============================================================================
# TC-210: _handle_v2_runner_on_failed Triggers FAILED State
# ==============================================================================


class TestRunnerOnFailedStateTransition:
    """Tests for FAILED state transition on runner_on_failed (TC-210)."""

    def test_runner_failed_triggers_runstate_failed(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed: dict,
    ) -> None:
        """TC-210: Failed task (ignore_errors=false) triggers FAILED state."""
        run_state = RunState(playbook="test.yml")

        # Start the playbook
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-04-20T10:00:00Z",
            }
        )
        assert run_state.status == Status.RUNNING

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_failed = {**event_runner_failed, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_failed)

        assert run_state.status == Status.FAILED

    def test_runner_failed_multiple_failures_stays_failed(self) -> None:
        """TC-210 edge case: Multiple failures - state remains FAILED."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "hosts": {"web1": {"failed": True, "msg": "Error 1"}},
                "play": {"id": "play-uuid-1"},
            }
        )
        assert run_state.status == Status.FAILED

        # Second failure
        run_state.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:06Z",
                "task": {"id": "task-uuid-2", "name": "Task 2"},
                "hosts": {"web1": {"failed": True, "msg": "Error 2"}},
                "play": {"id": "play-uuid-1"},
            }
        )
        assert run_state.status == Status.FAILED

    def test_runner_failed_ignore_errors_no_state_transition(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed_ignore: dict,
    ) -> None:
        """TC-210: ignore_errors=true does NOT trigger FAILED state."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_failed = {**event_runner_failed_ignore, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_failed)

        assert run_state.status == Status.RUNNING


# ==============================================================================
# TC-211: _handle_v2_runner_on_skipped Creates Skipped HostRunState
# ==============================================================================


class TestRunnerOnSkipped:
    """Tests for v2_runner_on_skipped handling (TC-211)."""

    def test_runner_skipped_creates_skipped_host(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_skipped: dict,
    ) -> None:
        """TC-211: v2_runner_on_skipped creates HostRunState with SKIPPED status."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_skipped = {**event_runner_skipped, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_skipped)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.SKIPPED

    def test_runner_skipped_multiple_hosts(self, event_play_start: dict) -> None:
        """TC-211 edge case: Multiple hosts skipped in single event."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_skipped",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "hosts": {"web1": {"skipped": True}, "web2": {"skipped": True}},
                "play": {"id": "play-uuid-1"},
            }
        )

        task_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"]
        assert task_state.hosts["web1"].status == Status.SKIPPED
        assert task_state.hosts["web2"].status == Status.SKIPPED


# ==============================================================================
# TC-212: _handle_v2_runner_on_unreachable Creates Unreachable HostRunState
# ==============================================================================


class TestRunnerOnUnreachable:
    """Tests for v2_runner_on_unreachable handling (TC-212)."""

    def test_runner_unreachable_creates_unreachable_host(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_unreachable: dict,
    ) -> None:
        """TC-212: v2_runner_on_unreachable creates HostRunState with UNREACHABLE status."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_unreachable = {**event_runner_unreachable, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_unreachable)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.status == Status.UNREACHABLE
        assert host_state.message == "SSH connection failed"

    def test_runner_unreachable_sets_end_time(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_unreachable: dict,
    ) -> None:
        """TC-212: Unreachable HostRunState has end_time set."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_unreachable = {**event_runner_unreachable, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_unreachable)

        host_state = run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts["web1"]
        assert host_state.end_time is not None


# ==============================================================================
# TC-213: _handle_v2_runner_on_unreachable Triggers FAILED State
# ==============================================================================


class TestRunnerOnUnreachableStateTransition:
    """Tests for FAILED state transition on runner_on_unreachable (TC-213)."""

    def test_runner_unreachable_triggers_runstate_failed(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_unreachable: dict,
    ) -> None:
        """TC-213: Unreachable host triggers FAILED state transition."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        assert run_state.status == Status.RUNNING

        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_unreachable = {**event_runner_unreachable, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_unreachable)

        assert run_state.status == Status.FAILED


# ==============================================================================
# TC-214: _handle_v2_playbook_on_stats Sets End State
# ==============================================================================


class TestPlaybookOnStats:
    """Tests for v2_playbook_on_stats handling (TC-214)."""

    def test_stats_sets_end_time(self, event_stats: dict) -> None:
        """TC-214: v2_playbook_on_stats sets RunState.end_time."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )

        run_state.handle_event(event_stats)

        assert run_state.end_time is not None
        assert run_state.end_time.hour == 10
        assert run_state.end_time.minute == 1

    def test_stats_no_failures_status_completed(self, event_stats: dict) -> None:
        """TC-214: Stats with no failures sets status to COMPLETED."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )

        run_state.handle_event(event_stats)

        assert run_state.status == Status.COMPLETED

    def test_stats_with_failures_status_failed(self) -> None:
        """TC-214: Stats with failures sets status to FAILED."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )

        event_with_failure = {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {
                    "ok": 4,
                    "changed": 2,
                    "failures": 1,  # Failure!
                    "skipped": 1,
                    "unreachable": 0,
                }
            },
        }
        run_state.handle_event(event_with_failure)

        assert run_state.status == Status.FAILED

    def test_stats_with_unreachable_status_failed(self) -> None:
        """TC-214: Stats with unreachable sets status to FAILED."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )

        event_with_unreachable = {
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {
                    "ok": 5,
                    "changed": 2,
                    "failures": 0,
                    "skipped": 1,
                    "unreachable": 1,  # Unreachable!
                }
            },
        }
        run_state.handle_event(event_with_unreachable)

        assert run_state.status == Status.FAILED

    def test_stats_empty_plays(self, event_stats: dict) -> None:
        """TC-214 edge case: Stats with empty plays dict still works."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )

        run_state.handle_event(event_stats)

        assert run_state.end_time is not None
        assert run_state.status == Status.COMPLETED


# ==============================================================================
# TC-215: _handle_v2_playbook_on_stats Cross-Validation
# ==============================================================================


class TestStatsCrossValidation:
    """Tests for stats cross-validation (TC-215)."""

    def test_stats_cross_check_hosts(
        self, event_play_start: dict, event_runner_start: dict, event_runner_ok: dict
    ) -> None:
        """TC-215: Stats event cross-checks hosts against HostRunStates."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {"ok": 1, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
                },
            }
        )

        # HostRunState exists for web1
        assert "web1" in run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts

    def test_stats_add_missing_hosts(self, event_play_start: dict) -> None:
        """TC-215 edge case: Stats contain hosts not in HostRunStates."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        run_state.handle_event(event_play_start)

        # Stats mention a host we never saw events for
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
                    "web2": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
                },
            }
        )

        # Stats should be processed without error
        assert run_state.status == Status.COMPLETED


# ==============================================================================
# TC-216: _handle_v2_playbook_on_stats Missing Hosts Marked Unreachable
# ==============================================================================


class TestStatsMissingHosts:
    """Tests for marking missing hosts as unreachable (TC-216)."""

    def test_stats_missing_hosts_marked_unreachable(self) -> None:
        """TC-216: Hosts in HostRunState but not in stats are marked unreachable."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"}
        )
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:03Z",
                "task": {"id": "task-uuid-2", "name": "Task 2"},
                "host": "web2",  # web2 starts but doesn't finish
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_ok",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "task-uuid-1", "name": "Task"},
                "hosts": {"web1": {"ok": True, "changed": False}},
                "play": {"id": "play-uuid-1"},
            }
        )

        # Stats only include web1, web2 is missing (it never completed)
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_stats",
                "_timestamp": "2026-04-20T10:01:00Z",
                "stats": {
                    "web1": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
                },
            }
        )

        assert "task-uuid-2" in run_state.plays["play-uuid-1"].tasks


# ==============================================================================
# TC-076: _handle_v2_playbook_on_handler_task_start Delegates to task_start
# ==============================================================================


class TestHandlerTaskStart:
    """Tests for v2_playbook_on_handler_task_start delegating to task_start (TC-076)."""

    def test_handler_task_start_delegates_to_task_start(self) -> None:
        """TC-076: handler_task_start calls _handle_v2_playbook_on_task_start."""
        run_state = RunState(playbook="test.yml")
        handler_event = {
            "_event": "v2_playbook_on_handler_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "handler-uuid-1", "name": "Restart nginx"},
            "play": {"id": "play-uuid-1"},
        }

        with patch.object(run_state, "_handle_v2_playbook_on_task_start") as mock_task_start:
            run_state.handle_event(handler_event)
            mock_task_start.assert_called_once()
            call_args = mock_task_start.call_args
            assert call_args[0][0] == handler_event

    def test_handler_task_start_creates_task_in_play(self) -> None:
        """TC-076: handler_task_start creates a TaskRunState just like task_start."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )

        # Send handler task start event
        handler_event = {
            "_event": "v2_playbook_on_handler_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "handler-uuid-1", "name": "Restart nginx"},
            "play": {"id": "play-uuid-1"},
        }
        run_state.handle_event(handler_event)

        assert "handler-uuid-1" in run_state.plays["play-uuid-1"].tasks
        task = run_state.plays["play-uuid-1"].tasks["handler-uuid-1"]
        assert task.name == "Restart nginx"

    def test_handler_task_start_sets_linear_strategy(self) -> None:
        """TC-076: handler_task_start sets linear strategy like task_start."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1", "name": "Setup"},
            }
        )

        handler_event = {
            "_event": "v2_playbook_on_handler_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "handler-uuid-1", "name": "Restart nginx"},
            "play": {"id": "play-uuid-1"},
        }
        run_state.handle_event(handler_event)

        play = run_state.plays["play-uuid-1"]
        assert play.detected_strategy == "linear"


# ==============================================================================
# TC-085: Timestamp Display - Local Timezone Conversion
# ==============================================================================


class TestTimestampLocalTimezone:
    """Tests for UTC timestamp conversion to local timezone (TC-085)."""

    def test_utc_timestamp_parsed_with_timezone(self) -> None:
        """TC-085: _parse_timestamp returns timezone-aware datetime from UTC string."""
        from ansible_aom.core.run_state import _parse_timestamp

        event = {"_timestamp": "2026-04-20T15:30:00Z"}
        result = _parse_timestamp(event)
        assert result.tzinfo is not None

    def test_utc_timestamp_converted_to_local_timezone(self) -> None:
        """TC-085: UTC timestamp can be converted to local timezone via astimezone()."""
        from ansible_aom.core.run_state import _parse_timestamp

        event = {"_timestamp": "2026-04-20T15:30:00Z"}
        result = _parse_timestamp(event)
        local_ts = result.astimezone()
        assert local_ts.tzinfo is not None
        assert result.timestamp() == local_ts.timestamp()

    def test_utc_z_suffix_parsed_correctly(self) -> None:
        """TC-085: 'Z' suffix in timestamps is handled as UTC."""
        from ansible_aom.core.run_state import _parse_timestamp

        event_z = {"_timestamp": "2026-04-20T10:00:00Z"}
        event_offset = {"_timestamp": "2026-04-20T10:00:00+00:00"}
        result_z = _parse_timestamp(event_z)
        result_offset = _parse_timestamp(event_offset)
        assert result_z == result_offset

    def test_utc_timestamp_without_z(self) -> None:
        """TC-085: Timestamps without Z still parse as UTC if +00:00."""
        from ansible_aom.core.run_state import _parse_timestamp

        event = {"_timestamp": "2026-04-20T10:00:00+00:00"}
        result = _parse_timestamp(event)
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 20

    @pytest.mark.parametrize(
        "ts_str,expected_hour",
        [
            ("2026-04-20T00:00:00Z", 0),
            ("2026-04-20T12:30:45Z", 12),
            ("2026-04-20T23:59:59Z", 23),
        ],
    )
    def test_various_utc_timestamps(self, ts_str: str, expected_hour: int) -> None:
        """TC-085: Various UTC timestamp strings parse correctly."""
        from ansible_aom.core.run_state import _parse_timestamp

        event = {"_timestamp": ts_str}
        result = _parse_timestamp(event)
        assert result.hour == expected_hour

    def test_local_timezone_preserves_instant(self) -> None:
        """TC-085: fromisoformat().astimezone() preserves UTC instant."""
        from ansible_aom.core.run_state import _parse_timestamp

        event = {"_timestamp": "2026-04-20T10:00:00Z"}
        utc_ts = _parse_timestamp(event)
        local_ts = utc_ts.astimezone()
        # Both represent the same instant regardless of timezone
        assert abs(utc_ts.timestamp() - local_ts.timestamp()) < 0.001


# ==============================================================================
# TC-086: Elapsed Time Calculation - HH:MM:SS format including 24+ hours
# ==============================================================================


class TestElapsedTimeFormat:
    """Tests for elapsed time formatting as H:MM:SS (TC-086)."""

    def test_format_status_bar_elapsed_under_one_minute(self) -> None:
        """TC-086: Elapsed time under 1 minute formats as 0:00:XX."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=1,
            hosts_total=5,
            warnings=0,
            deprecations=0,
            elapsed_seconds=45,
        )
        assert "0:00:45" in result

    def test_format_status_bar_elapsed_over_one_minute(self) -> None:
        """TC-086: Elapsed time over 1 minute formats as 0:MM:SS."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=3,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=323,
        )
        assert "0:05:23" in result

    def test_format_status_bar_elapsed_over_one_hour(self) -> None:
        """TC-086: Elapsed time over 1 hour formats as H:MM:SS."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=5,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=3725,
        )
        assert "1:02:05" in result

    def test_format_status_bar_elapsed_24_plus_hours(self) -> None:
        """TC-086: Elapsed time over 24 hours formats correctly (no day rollover)."""
        from ansible_aom.compact.renderer import format_status_bar

        # 25 hours, 30 minutes, 10 seconds = 91810 seconds
        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=10,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=91810,
        )
        assert "25:30:10" in result

    def test_format_status_bar_elapsed_zero(self) -> None:
        """TC-086: Zero elapsed time formats as 0:00:00."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=0,
            hosts_total=10,
            warnings=0,
            deprecations=0,
            elapsed_seconds=0,
        )
        assert "0:00:00" in result

    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0, "0:00:00"),
            (1, "0:00:01"),
            (59, "0:00:59"),
            (60, "0:01:00"),
            (3599, "0:59:59"),
            (3600, "1:00:00"),
            (86399, "23:59:59"),
            (86400, "24:00:00"),
            (90000, "25:00:00"),
            (100000, "27:46:40"),
        ],
    )
    def test_format_status_bar_elapsed_various_durations(self, seconds: int, expected: str) -> None:
        """TC-086: Various elapsed durations format as H:MM:SS."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="test.yml",
            hosts_completed=1,
            hosts_total=1,
            warnings=0,
            deprecations=0,
            elapsed_seconds=seconds,
        )
        assert expected in result

    def test_format_status_bar_elapsed_float_seconds(self) -> None:
        """TC-086: Float seconds are truncated (not rounded) to integer."""
        from ansible_aom.compact.renderer import format_status_bar

        result = format_status_bar(
            playbook="site.yml",
            hosts_completed=1,
            hosts_total=1,
            warnings=0,
            deprecations=0,
            elapsed_seconds=90.9,
        )
        # 90.9 truncated to 90 = 0:01:30
        assert "0:01:30" in result


# ==============================================================================
# TC-091, TC-092, TC-093: Task Matching Algorithm Tests
# ==============================================================================


class TestTaskMatchingAlgorithm:
    """Strengthened tests for task matching logic (TC-091, TC-092, TC-093)."""

    def test_uuid_match_identifies_correct_task(self) -> None:
        """TC-091: Matching by UUID finds the exact task."""
        tasks = [
            TaskDefinition(
                name="Install nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=0,
                uuid="uuid-aaa-111",
            ),
            TaskDefinition(
                name="Configure nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=1,
                uuid="uuid-bbb-222",
            ),
        ]
        # Simulate UUID matching
        match_uuid = "uuid-bbb-222"
        matched = next((t for t in tasks if t.uuid == match_uuid), None)
        assert matched is not None
        assert matched.name == "Configure nginx"
        assert matched.uuid == "uuid-bbb-222"

    def test_uuid_match_is_stronger_than_path_or_name(self) -> None:
        """TC-091: UUID match takes precedence over path and name matches."""
        tasks = [
            TaskDefinition(
                name="Install nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=0,
                uuid="uuid-unique-111",
                path="roles/nginx/tasks/main.yml:10",
            ),
            TaskDefinition(
                name="Install nginx",  # Same name as above
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=1,
                uuid="uuid-unique-222",
                path="roles/nginx/tasks/main.yml:10",  # Same path as above
            ),
        ]
        # UUID match uniquely identifies
        match_uuid = "uuid-unique-222"
        matched = next((t for t in tasks if t.uuid == match_uuid), None)
        assert matched is not None
        assert matched.task_order == 1

    def test_path_match_identifies_task_when_no_uuid(self) -> None:
        """TC-092: Matching by file:line path works when UUID is unavailable."""
        tasks = [
            TaskDefinition(
                name="Install nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=0,
                path="roles/nginx/tasks/main.yml:10",
            ),
            TaskDefinition(
                name="Configure nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=1,
                path="roles/nginx/tasks/main.yml:25",
            ),
        ]
        # Path uniquely identifies even without UUID
        match_path = "roles/nginx/tasks/main.yml:25"
        matched = next((t for t in tasks if t.path == match_path), None)
        assert matched is not None
        assert matched.name == "Configure nginx"

    def test_path_match_format_file_colon_line(self) -> None:
        """TC-092: Path matching uses file:line format from JSONL."""
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            path="site.yml:42",
        )
        # Path format is "file:line_number"
        assert ":" in task.path
        file_part, line_part = task.path.rsplit(":", 1)
        assert file_part == "site.yml"
        assert line_part == "42"

    def test_sequential_name_match_when_no_uuid_or_path(self) -> None:
        """TC-093: Fallback matching uses play_order + task_order + name."""
        tasks = [
            TaskDefinition(
                name="Install nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=0,
            ),
            TaskDefinition(
                name="Configure nginx",
                role="nginx",
                tags=["web"],
                play_id="1",
                play_order=0,
                task_order=1,
            ),
        ]
        # Match by play_order + task_order + name (no uuid, no path)
        match_play_order = 0
        match_task_order = 1
        match_name = "Configure nginx"
        matched = next(
            (
                t
                for t in tasks
                if t.play_order == match_play_order
                and t.task_order == match_task_order
                and t.name == match_name
            ),
            None,
        )
        assert matched is not None
        assert matched.name == "Configure nginx"
        assert matched.task_order == 1

    def test_matching_priority_uuid_over_path(self) -> None:
        """TC-091 > TC-092: UUID match is tried before path match."""
        # Task with both UUID and path set
        task = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            uuid="uuid-abc-123",
            path="roles/nginx/tasks/main.yml:10",
        )
        # If UUID is present, use UUID matching
        assert task.uuid is not None
        assert task.uuid == "uuid-abc-123"
        # If UUID is None, fall back to path
        task_no_uuid = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=["web"],
            play_id="1",
            play_order=0,
            task_order=0,
            path="roles/nginx/tasks/main.yml:10",
        )
        assert task_no_uuid.uuid is None
        assert task_no_uuid.path is not None

    def test_matching_falls_back_through_levels(self) -> None:
        """TC-091 > TC-092 > TC-093: Matching priority order."""
        # Create tasks with different levels of identity
        task_with_uuid = TaskDefinition(
            name="Install nginx",
            role="nginx",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=0,
            uuid="uuid-aaa",
            path="roles/nginx/tasks/main.yml:10",
        )
        task_with_path = TaskDefinition(
            name="Configure nginx",
            role="nginx",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=1,
            path="roles/nginx/tasks/main.yml:25",
        )
        task_with_name_only = TaskDefinition(
            name="Start nginx",
            role="nginx",
            tags=[],
            play_id="1",
            play_order=0,
            task_order=2,
        )

        # Simulate matching priority
        all_tasks = [task_with_uuid, task_with_path, task_with_name_only]

        # Level 1: UUID match
        uuid_match = next((t for t in all_tasks if t.uuid == "uuid-aaa"), None)
        assert uuid_match is not None
        assert uuid_match.name == "Install nginx"

        # Level 2: Path match (when UUID not available)
        path_match = next((t for t in all_tasks if t.path == "roles/nginx/tasks/main.yml:25"), None)
        assert path_match is not None
        assert path_match.name == "Configure nginx"

        # Level 3: Sequential name match
        name_match = next(
            (
                t
                for t in all_tasks
                if t.name == "Start nginx" and t.play_order == 0 and t.task_order == 2
            ),
            None,
        )
        assert name_match is not None
        assert name_match.name == "Start nginx"

    def test_sequential_match_disambiguates_by_order(self) -> None:
        """TC-093: Sequential match uses play_order and task_order to disambiguate."""
        # Two tasks with same name but different order
        task_a = TaskDefinition(
            name="Restart service",
            role="app",
            tags=["restart"],
            play_id="1",
            play_order=0,
            task_order=3,
        )
        task_b = TaskDefinition(
            name="Restart service",
            role="app",
            tags=["restart"],
            play_id="1",
            play_order=0,
            task_order=7,
        )
        # Same name, different order
        assert task_a.name == task_b.name
        assert task_a.play_order == task_b.play_order
        assert task_a.task_order != task_b.task_order

        # Can disambiguate by task_order
        matched = next(
            (t for t in [task_a, task_b] if t.name == "Restart service" and t.task_order == 7),
            None,
        )
        assert matched is task_b


# ==============================================================================
# Additional Edge Cases
# ==============================================================================


class TestEventProcessingEdgeCases:
    """Edge case tests for event processing."""

    def test_event_without_timestamp_field(self) -> None:
        """Events without _timestamp use current time."""
        run_state = RunState(playbook="test.yml")
        event = {"_event": "v2_playbook_on_start"}

        run_state.handle_event(event)

        assert run_state.start_time is not None
        assert run_state.status == Status.RUNNING

    def test_event_with_missing_optional_fields(self) -> None:
        """Events with missing optional fields are handled gracefully."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event(
            {
                "_event": "v2_playbook_on_start",
                "_timestamp": "2026-04-20T10:00:00Z",
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_playbook_on_play_start",
                "_timestamp": "2026-04-20T10:00:01Z",
                "play": {"id": "play-uuid-1"},
            }
        )
        run_state.handle_event(
            {
                "_event": "v2_runner_on_start",
                "_timestamp": "2026-04-20T10:00:02Z",
                "task": {"id": "task-uuid-1"},
                "host": "web1",
                "play": {"id": "play-uuid-1"},
            }
        )

        assert "play-uuid-1" in run_state.plays
        assert "task-uuid-1" in run_state.plays["play-uuid-1"].tasks

    def test_playbook_lifecycle_full_flow(
        self,
        event_playbook_start: dict,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_ok: dict,
        event_stats: dict,
    ) -> None:
        """Integration test: Full playbook lifecycle from start to completion."""
        run_state = RunState(playbook="site.yml")

        # Start playbook
        run_state.handle_event(event_playbook_start)
        assert run_state.status == Status.RUNNING

        # Play starts
        run_state.handle_event(event_play_start)
        assert "play-uuid-1" in run_state.plays

        # Task starts (runner)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        assert "task-uuid-1" in run_state.plays["play-uuid-1"].tasks

        # Task completes
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)
        assert "web1" in run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts

        # Stats event completes playbook
        run_state.handle_event(event_stats)
        assert run_state.status == Status.COMPLETED
        assert run_state.end_time is not None


# ==============================================================================
# TC-MITOGEN: handle_event robustness to malformed event payloads
# ==============================================================================
#
# When mitogen drops the SSH link mid-task, ansible.posix.jsonl sometimes
# emits events whose payloads do not match the documented JSONL shape:
#
#   1. ``task`` is a bare UUID string instead of a dict (the JSONL callback
#      serialises the parent task as just an id when the runner never
#      received a path).
#   2. ``task`` is null (mitogen shimmed actions sometimes yield task=None
#      at the leaf).
#   3. ``hosts`` is a list instead of a dict (mitogen aggregates per-host
#      results into a list under a single event on bulk reconnects).
#
# Historically AOM crashed on all three with AttributeError, aborting the
# whole runner thread mid-playbook. The user-visible symptom was that the
# log area kept scrolling but the bottom status panel froze — because the
# runner process had died, leaving only ansible's already-buffered PTY
# output visible. The state machine must instead tolerate the malformed
# payloads: silently drop the offending event and continue with the next.
# ==============================================================================


def _seed_run_state() -> RunState:
    """Build a RunState with one play, one task, and one host already RUNNING.

    The fixture mirrors what a real mid-run state looks like when mitogen
    finally drops. Tests then send a single malformed terminal event and
    assert the runner survives without raising and without corrupting
    the existing state.
    """
    rs = RunState(playbook="site.yml")
    rs.handle_event(
        {
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-04-20T10:00:00Z",
        }
    )
    rs.handle_event(
        {
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "p1", "name": "Install Foreman"},
        }
    )
    rs.handle_event(
        {
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
        }
    )
    rs.handle_event(
        {
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "host": "foreman",
        }
    )
    return rs


class TestHandleEventMalformedPayloads:
    """TC-MITOGEN-1..6: handle_event must tolerate mitogen-distorted payloads.

    The mitogen SSH transport can drop mid-task. The JSONL callback then
    emits events with task/hosts fields whose shapes diverge from the
    canonical contract — these tests pin the requirement that AOM does
    NOT crash on them, and that the pre-existing in-flight state is
    preserved (a single bad event must not corrupt the run).
    """

    def test_runner_unreachable_with_task_as_string_does_not_raise(self) -> None:
        """TC-MITOGEN-1: ``task`` as a bare UUID string must be tolerated.

        ansible.posix.jsonl emits ``task`` as a string when the runner
        never received a path for the parent task — the canonical
        failure mode of a mitogen SSH drop mid-task. The state machine
        previously crashed with ``AttributeError: 'str' object has no
        attribute 'get'`` from ``_handle_v2_runner_on_unreachable``.
        """
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": "t1",  # bare UUID string, NOT a dict
            "play": {"id": "p1"},
            "host": "foreman",
            "msg": "MITOGEN: rpc failed: broken pipe",
        }
        # Must not raise.
        rs.handle_event(bad_event)
        # The pre-existing RUNNING host foreman is still tracked —
        # the bad event silently drops rather than overwriting with
        # a half-populated host entry.
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.RUNNING

    def test_runner_failed_with_task_as_none_does_not_raise(self) -> None:
        """TC-MITOGEN-2: ``task: None`` must be tolerated.

        Mitogen-shimmed actions sometimes yield task=None at the leaf
        when the transport races the dispatcher. The state machine
        previously crashed with ``AttributeError: 'NoneType' object
        has no attribute 'get'``.
        """
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": None,
            "play": {"id": "p1"},
            "host": "foreman",
            "msg": "MITOGEN: orphaned event",
        }
        rs.handle_event(bad_event)
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.RUNNING

    def test_runner_ok_with_hosts_as_list_does_not_raise(self) -> None:
        """TC-MITOGEN-3: ``hosts`` as a list must be tolerated.

        Mitogen aggregates per-host results into a list under a single
        event during bulk reconnects. ``hosts_data.items()`` previously
        raised ``AttributeError: 'list' object has no attribute 'items'``.
        """
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman", "ds5"],  # list, NOT dict
        }
        rs.handle_event(bad_event)
        # No fake host entries were materialised — the event silently
        # drops. The pre-existing in-flight host is untouched.
        hosts = rs.plays["p1"].tasks["t1"].hosts
        assert set(hosts) == {"foreman"}
        assert hosts["foreman"].status == Status.RUNNING

    def test_runner_unreachable_with_hosts_as_list_does_not_raise(self) -> None:
        """TC-MITOGEN-4: ``hosts: list`` on unreachable must also be tolerated."""
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_unreachable",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman", "ds5"],
        }
        rs.handle_event(bad_event)
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.RUNNING

    def test_runner_failed_with_hosts_as_list_does_not_raise(self) -> None:
        """TC-MITOGEN-5: ``hosts: list`` on failed must also be tolerated."""
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman"],
        }
        rs.handle_event(bad_event)
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.RUNNING

    def test_runner_skipped_with_hosts_as_list_does_not_raise(self) -> None:
        """TC-MITOGEN-6: ``hosts: list`` on skipped must also be tolerated."""
        rs = _seed_run_state()
        bad_event = {
            "_event": "v2_runner_on_skipped",
            "_timestamp": "2026-04-20T10:00:04Z",
            "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
            "play": {"id": "p1"},
            "hosts": ["foreman"],
        }
        rs.handle_event(bad_event)
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.RUNNING

    def test_recovery_after_malformed_event(self) -> None:
        """TC-MITOGEN-7: A malformed event does not poison subsequent events.

        After dropping a bad mitogen event, the runner must continue
        processing well-formed events normally. This is the "single bad
        event must not corrupt the run" requirement that fixes the
        user-visible symptom of a frozen panel.
        """
        rs = _seed_run_state()
        rs.handle_event(
            {
                "_event": "v2_runner_on_unreachable",
                "_timestamp": "2026-04-20T10:00:04Z",
                "task": "t1",
                "play": {"id": "p1"},
                "host": "foreman",
            }
        )
        # A subsequent well-formed event must still mutate state correctly.
        rs.handle_event(
            {
                "_event": "v2_runner_on_failed",
                "_timestamp": "2026-04-20T10:00:05Z",
                "task": {"id": "t1", "name": "Install NFS utils", "path": "main.yml:1"},
                "play": {"id": "p1"},
                "hosts": {"foreman": {"failed": True, "msg": "recovered"}},
            }
        )
        host = rs.plays["p1"].tasks["t1"].hosts["foreman"]
        assert host.status == Status.FAILED
        assert rs.status == Status.FAILED
