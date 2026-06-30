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

    assert state == LivenessState(level="working", age_s=10, reason="silent")


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

    assert state == LivenessState(level="stuck", age_s=35, reason="stuck")


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


def test_age_seconds_truncates_toward_zero():
    tracker = HeartbeatTracker()
    tracker.note_bytes(now=100.0)

    # 1.9s elapsed should report age_s=1, not rounded to 2.
    assert tracker.state(now=101.9).age_s == 1


def test_silent_task_after_initial_byte_progresses_through_levels():
    """The real-world brew-install case: one byte at task start, then
    silence. The tracker must keep returning a state (LIVE → WORKING →
    STUCK), not None — otherwise the user sees no liveness indicator
    for the entire duration of the slow task."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)

    # Just after the task_start byte — LIVE.
    assert tracker.state(now=101.0) is not None
    assert tracker.state(now=101.0).level == "live"

    # 10s later, no further bytes — WORKING (because byte age 10 > live
    # threshold 5 but < stuck threshold 30).
    assert tracker.state(now=110.0).level == "working"

    # 35s later, no further bytes and no CPU samples — STUCK.
    assert tracker.state(now=135.0).level == "stuck"


def test_cpu_activity_promotes_state_to_live_during_silent_window():
    """User-facing case: ansible-playbook is silent for >5s but its CPU
    sampler shows the process tree is busy (e.g. spawning module
    subprocesses, compiling modules, running ``brew``). The grey ○ should
    flip back to a green ● so the user knows AOM is observing genuine
    activity. This is the inverse of the existing stuck-rescue path:
    same CPU signal, applied earlier in the timeline."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    # 6s past last byte (out of LIVE window), but CPU was active 1s ago.
    tracker.note_cpu_sample(now=105.0, active=True)

    state = tracker.state(now=106.0)

    assert state.level == "live"
    assert state.age_s == 6  # age tracks last byte, not last CPU sample


def test_inactive_cpu_sample_does_not_promote_to_live():
    """An ``active=False`` sample is informational ('CPU was idle') and
    must not satisfy the CPU-promotion path."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    tracker.note_cpu_sample(now=105.0, active=False)

    state = tracker.state(now=106.0)

    assert state.level == "working"


def test_cpu_active_too_long_ago_does_not_promote_to_live():
    """CPU samples older than the live window stop counting as 'recent'.
    They can still rescue from STUCK (existing behaviour) but cannot
    keep the dot green."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    # Active 10s ago — past the 5s live window but inside the 30s stuck window.
    tracker.note_cpu_sample(now=110.0, active=True)

    state = tracker.state(now=120.0)

    assert state.level == "working"


def test_liveness_state_reason_field_defaults():
    """``reason`` annotates why the level is what it is. Backwards-compat:
    existing call sites that pass only level + age_s must still work."""
    state = LivenessState(level="live", age_s=3)
    assert state.reason == "pty"


def test_reason_pty_for_recent_bytes():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)

    assert tracker.state(now=102.0).reason == "pty"


def test_reason_cpu_when_promoted_from_working_to_live():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    tracker.note_cpu_sample(now=107.0, active=True)

    state = tracker.state(now=108.0)

    assert state.level == "live"
    assert state.reason == "cpu"


def test_reason_silent_when_working_via_byte_age_only():
    """No CPU info available (sampler hasn't reported yet, or always
    inactive) — the WORKING dot means 'silent, but not yet stuck'."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)

    state = tracker.state(now=110.0)

    assert state.level == "working"
    assert state.reason == "silent"


def test_reason_cpu_for_stuck_window_rescue():
    """Bytes long-stale, but CPU active recently → WORKING (not STUCK).
    The reason field should make this distinction visible to the UI."""
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)
    # CPU was active 15s ago — past the live window but inside stuck.
    tracker.note_cpu_sample(now=135.0, active=True)

    state = tracker.state(now=150.0)

    assert state.level == "working"
    assert state.reason == "cpu"


def test_reason_stuck_when_no_signals_at_all():
    tracker = HeartbeatTracker(live_threshold_s=5.0, stuck_threshold_s=30.0)
    tracker.note_bytes(now=100.0)

    state = tracker.state(now=135.0)

    assert state.level == "stuck"
    assert state.reason == "stuck"


def test_liveness_state_is_frozen_dataclass():
    state = LivenessState(level="live", age_s=3)
    with pytest.raises((AttributeError, Exception)):
        state.level = "stuck"  # type: ignore[misc]
