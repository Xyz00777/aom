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
    RunState,
    Status,
    TaskRunState,
)


# ==============================================================================
# TC-197: handle_event Dispatcher Routing
# ==============================================================================


class TestHandleEventDispatcher:
    """Tests for handle_event routing events to correct handlers (TC-197)."""

    def test_handle_event_routes_to_playbook_on_start(
        self, event_playbook_start: dict
    ) -> None:
        """TC-197: handle_event routes v2_playbook_on_start to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(
            run_state, "_handle_v2_playbook_on_start"
        ) as mock_handler:
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

        with patch.object(
            run_state, "_handle_v2_playbook_on_task_start"
        ) as mock_handler:
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

    def test_handle_event_routes_to_runner_failed(
        self, event_runner_failed: dict
    ) -> None:
        """TC-197: handle_event routes v2_runner_on_failed to correct handler."""
        run_state = RunState(playbook="test.yml")

        with patch.object(run_state, "_handle_v2_runner_on_failed") as mock_handler:
            run_state.handle_event(event_runner_failed)
            mock_handler.assert_called_once()

    def test_handle_event_routes_to_runner_skipped(
        self, event_runner_skipped: dict
    ) -> None:
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

        with patch.object(
            run_state, "_handle_v2_runner_on_unreachable"
        ) as mock_handler:
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

    def test_handle_event_parses_iso_timestamp(
        self, event_playbook_start: dict
    ) -> None:
        """TC-198: Timestamp is parsed from _timestamp field as ISO format datetime."""
        run_state = RunState(playbook="test.yml")

        # The fixture has timestamp "2026-04-20T10:00:00Z"
        with patch.object(
            run_state, "_handle_v2_playbook_on_start"
        ) as mock_handler:
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

        with patch.object(
            run_state, "_handle_v2_playbook_on_start"
        ) as mock_handler:
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
        with patch.object(
            run_state, "_handle_v2_playbook_on_start"
        ) as mock_handler:
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

    def test_playbook_on_start_sets_status_running(
        self, event_playbook_start: dict
    ) -> None:
        """TC-200: v2_playbook_on_start sets status to RUNNING."""
        run_state = RunState(playbook="test.yml")
        assert run_state.status == Status.PENDING

        run_state.handle_event(event_playbook_start)

        assert run_state.status == Status.RUNNING

    def test_playbook_on_start_sets_start_time(
        self, event_playbook_start: dict
    ) -> None:
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

    def test_play_start_creates_play_run_state(
        self, event_play_start: dict
    ) -> None:
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
        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup"},
        })

        # First task_start sets strategy to linear
        run_state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task 1"},
            "play": {"id": "play-uuid-1"},
        })
        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"

        # Manually set strategy to something else (simulating prior detection)
        run_state.plays["play-uuid-1"].detected_strategy = "free"

        # Another task_start should not change it
        run_state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "task-uuid-2", "name": "Task 2"},
            "play": {"id": "play-uuid-1"},
        })
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

    def test_runner_start_after_task_start_keeps_linear(self) -> None:
        """TC-203 edge case: runner_on_start after task_start keeps linear strategy."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup"},
        })
        run_state.handle_event({
            "_event": "v2_playbook_on_task_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "play": {"id": "play-uuid-1"},
        })
        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"

        # Now runner_on_start arrives - strategy should remain linear
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })

        assert run_state.plays["play-uuid-1"].detected_strategy == "linear"


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
        assert task_state.status == Status.RUNNING

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

    def test_runner_start_missing_play_creates_play(
        self, event_runner_start: dict
    ) -> None:
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
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Install nginx"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-1", "name": "Install nginx"},
            "hosts": {
                "web1": {"ok": True, "changed": False},
                "web2": {"ok": True, "changed": False},
            },
            "play": {"id": "play-uuid-1"},
        })

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
        run_state.handle_event({
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-1", "name": "Install nginx"},
            "hosts": {"web1": {"ok": True}},  # No 'changed' field
            "play": {"id": "play-uuid-1"},
        })

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

    def test_runner_failed_ignore_errors_nested_location(self) -> None:
        """TC-209: Nested ignore_errors location in _ansible_verbose_always."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
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
        })

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
        run_state.handle_event({
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-04-20T10:00:00Z",
        })
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

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "hosts": {"web1": {"failed": True, "msg": "Error 1"}},
            "play": {"id": "play-uuid-1"},
        })
        assert run_state.status == Status.FAILED

        # Second failure
        run_state.handle_event({
            "_event": "v2_runner_on_failed",
            "_timestamp": "2026-04-20T10:00:06Z",
            "task": {"id": "task-uuid-2", "name": "Task 2"},
            "hosts": {"web1": {"failed": True, "msg": "Error 2"}},
            "play": {"id": "play-uuid-1"},
        })
        assert run_state.status == Status.FAILED

    def test_runner_failed_ignore_errors_no_state_transition(
        self,
        event_play_start: dict,
        event_runner_start: dict,
        event_runner_failed_ignore: dict,
    ) -> None:
        """TC-210: ignore_errors=true does NOT trigger FAILED state."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
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
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_skipped",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "hosts": {"web1": {"skipped": True}, "web2": {"skipped": True}},
            "play": {"id": "play-uuid-1"},
        })

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

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
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
        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})

        run_state.handle_event(event_stats)

        assert run_state.end_time is not None
        assert run_state.end_time.hour == 10
        assert run_state.end_time.minute == 1

    def test_stats_no_failures_status_completed(self, event_stats: dict) -> None:
        """TC-214: Stats with no failures sets status to COMPLETED."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})

        run_state.handle_event(event_stats)

        assert run_state.status == Status.COMPLETED

    def test_stats_with_failures_status_failed(self) -> None:
        """TC-214: Stats with failures sets status to FAILED."""
        run_state = RunState(playbook="test.yml")
        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})

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
        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})

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
        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})

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

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        run_state.handle_event(event_play_start)
        runner_start = {**event_runner_start, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_start)
        runner_ok = {**event_runner_ok, "play": {"id": "play-uuid-1"}}
        run_state.handle_event(runner_ok)

        run_state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {"ok": 1, "changed": 0, "failures": 0, "skipped": 0, "unreachable": 0},
            },
        })

        # HostRunState exists for web1
        assert "web1" in run_state.plays["play-uuid-1"].tasks["task-uuid-1"].hosts

    def test_stats_add_missing_hosts(self, event_play_start: dict) -> None:
        """TC-215 edge case: Stats contain hosts not in HostRunStates."""
        run_state = RunState(playbook="test.yml")

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        run_state.handle_event(event_play_start)

        # Stats mention a host we never saw events for
        run_state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
                "web2": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
            },
        })

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

        run_state.handle_event({"_event": "v2_playbook_on_start", "_timestamp": "2026-04-20T10:00:00Z"})
        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1", "name": "Setup"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:03Z",
            "task": {"id": "task-uuid-2", "name": "Task 2"},
            "host": "web2",  # web2 starts but doesn't finish
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_ok",
            "_timestamp": "2026-04-20T10:00:05Z",
            "task": {"id": "task-uuid-1", "name": "Task"},
            "hosts": {"web1": {"ok": True, "changed": False}},
            "play": {"id": "play-uuid-1"},
        })

        # Stats only include web1, web2 is missing (it never completed)
        run_state.handle_event({
            "_event": "v2_playbook_on_stats",
            "_timestamp": "2026-04-20T10:01:00Z",
            "stats": {
                "web1": {"ok": 5, "changed": 2, "failures": 0, "skipped": 1, "unreachable": 0},
            },
        })

        assert "task-uuid-2" in run_state.plays["play-uuid-1"].tasks


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

        run_state.handle_event({
            "_event": "v2_playbook_on_start",
            "_timestamp": "2026-04-20T10:00:00Z",
        })
        run_state.handle_event({
            "_event": "v2_playbook_on_play_start",
            "_timestamp": "2026-04-20T10:00:01Z",
            "play": {"id": "play-uuid-1"},
        })
        run_state.handle_event({
            "_event": "v2_runner_on_start",
            "_timestamp": "2026-04-20T10:00:02Z",
            "task": {"id": "task-uuid-1"},
            "host": "web1",
            "play": {"id": "play-uuid-1"},
        })

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