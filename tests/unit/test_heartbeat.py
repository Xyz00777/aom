"""Tests for HeartbeatTracker (core/heartbeat.py).

The tracker derives a three-level liveness signal from two facts fed
in by the runner: when the last PTY byte arrived, and whether the
subprocess (plus children) has used CPU recently. All time is
injected as monotonic float seconds so tests can fast-forward without
``time.sleep`` or freezegun.
"""

from __future__ import annotations

import pytest

from ansible_aom.core.heartbeat import HeartbeatTracker, LivenessState


def test_state_is_none_before_any_bytes_observed():
    tracker = HeartbeatTracker()
    assert tracker.state(now=100.0) is None


def test_live_immediately_after_first_bytes():
    tracker = HeartbeatTracker()
    tracker.note_bytes(now=100.0)

    state = tracker.state(now=101.0)

    assert state == LivenessState(level="live", age_s=1)


def test_live_window_uses_configured_threshold():
    tracker = HeartbeatTracker(live_threshold_s=5.0)
    tracker.note_bytes(now=100.0)

    # Just inside the live window.
    assert tracker.state(now=104.9).level == "live"
    # Exactly at the boundary flips out of LIVE — strict less-than.
    assert tracker.state(now=105.0).level == "working"


def test_working_state_via_byte_age_alone():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)

    state = tracker.state(now=110.0)

    assert state == LivenessState(level="working", age_s=10)


def test_cpu_activity_keeps_state_working_past_stuck_threshold():
    """Bytes long ago, but CPU was active recently → still working, not stuck."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    # CPU was active 5 seconds before we ask — well within the stuck window.
    tracker.note_cpu_sample(now=145.0, active=True)

    state = tracker.state(now=150.0)

    assert state.level == "working"
    assert state.age_s == 50


def test_stuck_when_bytes_old_and_no_cpu_activity():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    tracker.note_cpu_sample(now=101.0, active=False)

    state = tracker.state(now=135.0)

    assert state == LivenessState(level="stuck", age_s=35)


def test_stuck_when_only_inactive_cpu_samples_received():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    # Multiple inactive samples should not rescue from STUCK.
    for t in (110.0, 120.0, 130.0):
        tracker.note_cpu_sample(now=t, active=False)

    assert tracker.state(now=135.0).level == "stuck"


def test_cpu_active_too_long_ago_does_not_rescue_from_stuck():
    """Active CPU sample older than stuck_threshold_s no longer counts."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    tracker.note_cpu_sample(now=101.0, active=True)  # ancient

    state = tracker.state(now=150.0)

    # 49s since the active CPU sample > 30s stuck threshold → no rescue.
    assert state.level == "stuck"


def test_new_bytes_return_tracker_to_live_after_stuck():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    assert tracker.state(now=140.0).level == "stuck"

    tracker.note_bytes(now=141.0)

    assert tracker.state(now=142.0).level == "live"


def test_reset_clears_observed_state():
    tracker = HeartbeatTracker()
    tracker.note_bytes(now=100.0)
    tracker.note_cpu_sample(now=101.0, active=True)

    tracker.reset()

    assert tracker.state(now=200.0) is None


def test_reset_then_new_task_starts_fresh():
    tracker = HeartbeatTracker()
    tracker.note_bytes(now=100.0)
    tracker.reset()
    tracker.note_bytes(now=200.0)

    assert tracker.state(now=201.0) == LivenessState(level="live", age_s=1)


def test_age_seconds_truncates_toward_zero():
    tracker = HeartbeatTracker()
    tracker.note_bytes(now=100.0)

    # 1.9s elapsed should report age_s=1, not rounded to 2.
    assert tracker.state(now=101.9).age_s == 1


def test_liveness_state_is_frozen_dataclass():
    state = LivenessState(level="live", age_s=3)
    with pytest.raises((AttributeError, Exception)):
        state.level = "stuck"  # type: ignore[misc]
