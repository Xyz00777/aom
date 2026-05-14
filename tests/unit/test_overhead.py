"""Tests for per-task overhead analysis (core/overhead.py).

The analyzer measures per-(host, task) wall-clock durations from JSONL
events and reports the lower-quartile floor as a proxy for "fork +
module-ship + Python-startup" cost that every task pays regardless of
its actual work. See docstring on ``analyze_overhead`` for the rationale.
"""

from __future__ import annotations

import pytest

from ansible_aom.core.overhead import OverheadStats, analyze_overhead


def _task_start(ts: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_playbook_on_task_start",
        "_timestamp": ts,
        "task": {"id": task_id, "name": f"Task {task_id}"},
    }


def _runner_ok(ts: str, host: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_ok",
        "_timestamp": ts,
        "task": {"id": task_id},
        "hosts": {host: {"ok": True}},
    }


def _runner_failed(ts: str, host: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_failed",
        "_timestamp": ts,
        "task": {"id": task_id},
        "hosts": {host: {"failed": True}},
    }


def _runner_unreachable(ts: str, host: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_unreachable",
        "_timestamp": ts,
        "task": {"id": task_id},
        "hosts": {host: {"unreachable": True}},
    }


def _runner_skipped(ts: str, host: str, task_id: str = "t1") -> dict:
    return {
        "_event": "v2_runner_on_skipped",
        "_timestamp": ts,
        "task": {"id": task_id},
        "hosts": {host: {"skipped": True}},
    }


def _stats(ts: str) -> dict:
    return {"_event": "v2_playbook_on_stats", "_timestamp": ts, "stats": {}}


def _playbook_start(ts: str) -> dict:
    return {"_event": "v2_playbook_on_start", "_timestamp": ts}


class TestEmptyAndDegenerate:
    def test_no_events(self) -> None:
        result = analyze_overhead([])
        assert result.samples == 0
        assert result.overhead_floor_s is None
        assert result.median_duration_s is None
        assert result.estimated_overhead_wall_s is None

    def test_only_metadata_events(self) -> None:
        result = analyze_overhead([_playbook_start("2026-04-20T10:00:00Z")])
        assert result.samples == 0
        assert result.overhead_floor_s is None

    def test_insufficient_samples(self) -> None:
        """Need at least 4 (host, task) samples to compute a defensible
        P25. Fewer than that returns sample count but no percentile."""
        events = [
            _task_start("2026-04-20T10:00:00Z", task_id="t1"),
            _runner_ok("2026-04-20T10:00:01Z", "h1", task_id="t1"),
            _task_start("2026-04-20T10:00:02Z", task_id="t2"),
            _runner_ok("2026-04-20T10:00:04Z", "h1", task_id="t2"),
        ]
        result = analyze_overhead(events)
        assert result.samples == 2
        assert result.overhead_floor_s is None

    def test_runner_event_without_matching_task_start_is_skipped(self) -> None:
        events = [_runner_ok("2026-04-20T10:00:01Z", "h1", task_id="t-orphan")]
        result = analyze_overhead(events)
        assert result.samples == 0


class TestBasicDurations:
    def test_floor_is_p25_of_durations(self) -> None:
        """Durations: 1, 2, 3, 4, 5 seconds — P25 = 2.0."""
        events = []
        for i, dur in enumerate([1, 2, 3, 4, 5], start=1):
            events.append(_task_start(f"2026-04-20T10:00:{i:02d}Z", task_id=f"t{i}"))
            events.append(
                _runner_ok(
                    f"2026-04-20T10:00:{i + dur:02d}Z", "h1", task_id=f"t{i}"
                )
            )
        result = analyze_overhead(events)
        assert result.samples == 5
        assert result.overhead_floor_s == pytest.approx(2.0, abs=0.001)
        assert result.median_duration_s == pytest.approx(3.0, abs=0.001)

    def test_all_runner_result_types_count(self) -> None:
        """ok / failed / unreachable / skipped all measure overhead — the
        fork happened either way, even if the module bailed early."""
        events = [
            _task_start("2026-04-20T10:00:00Z", task_id="t1"),
            _runner_ok("2026-04-20T10:00:01Z", "h1", task_id="t1"),
            _runner_failed("2026-04-20T10:00:02Z", "h2", task_id="t1"),
            _runner_unreachable("2026-04-20T10:00:03Z", "h3", task_id="t1"),
            _runner_skipped("2026-04-20T10:00:04Z", "h4", task_id="t1"),
        ]
        result = analyze_overhead(events)
        assert result.samples == 4
        assert result.distinct_hosts == 4
        assert result.distinct_tasks == 1


class TestMultiHostMultiTask:
    def test_distinct_counts(self) -> None:
        events = []
        for task_idx in range(4):
            tid = f"t{task_idx}"
            events.append(_task_start(f"2026-04-20T10:{task_idx:02d}:00Z", task_id=tid))
            for h in ("h1", "h2", "h3"):
                events.append(
                    _runner_ok(f"2026-04-20T10:{task_idx:02d}:01Z", h, task_id=tid)
                )
        result = analyze_overhead(events)
        assert result.samples == 12
        assert result.distinct_tasks == 4
        assert result.distinct_hosts == 3


class TestWallClockAndShare:
    def test_wall_clock_from_start_and_stats(self) -> None:
        events = [
            _playbook_start("2026-04-20T10:00:00Z"),
            _task_start("2026-04-20T10:00:01Z", task_id="t1"),
            _runner_ok("2026-04-20T10:00:02Z", "h1", task_id="t1"),
            _runner_ok("2026-04-20T10:00:02Z", "h2", task_id="t1"),
            _runner_ok("2026-04-20T10:00:02Z", "h3", task_id="t1"),
            _runner_ok("2026-04-20T10:00:02Z", "h4", task_id="t1"),
            _stats("2026-04-20T10:01:00Z"),
        ]
        result = analyze_overhead(events)
        assert result.wall_clock_s == pytest.approx(60.0, abs=0.001)

    def test_estimated_overhead_uses_distinct_task_count(self) -> None:
        """Overhead is paid once per task wall-clock (hosts parallelize).
        Floor=1s, 4 distinct tasks → estimated_overhead_wall_s = 4.0."""
        events = []
        for task_idx in range(4):
            tid = f"t{task_idx}"
            events.append(_task_start(f"2026-04-20T10:{task_idx:02d}:00Z", task_id=tid))
            for h in ("h1", "h2", "h3"):
                events.append(
                    _runner_ok(f"2026-04-20T10:{task_idx:02d}:01Z", h, task_id=tid)
                )
        result = analyze_overhead(events)
        assert result.overhead_floor_s == pytest.approx(1.0, abs=0.001)
        assert result.distinct_tasks == 4
        assert result.estimated_overhead_wall_s == pytest.approx(4.0, abs=0.001)

    def test_overhead_share_is_ratio(self) -> None:
        events = [_playbook_start("2026-04-20T10:00:00Z")]
        for task_idx in range(4):
            tid = f"t{task_idx}"
            events.append(_task_start(f"2026-04-20T10:{task_idx:02d}:00Z", task_id=tid))
            for h in ("h1", "h2", "h3"):
                events.append(
                    _runner_ok(f"2026-04-20T10:{task_idx:02d}:01Z", h, task_id=tid)
                )
        events.append(_stats("2026-04-20T10:10:00Z"))
        result = analyze_overhead(events)
        assert result.wall_clock_s == pytest.approx(600.0, abs=0.001)
        assert result.estimated_overhead_wall_s == pytest.approx(4.0, abs=0.001)
        assert result.overhead_share == pytest.approx(4.0 / 600.0, abs=0.0001)

    def test_overhead_share_clamped_to_one(self) -> None:
        """If our estimate exceeds wall-clock (rare, but possible with
        very short runs and slow per-task overhead), clamp to 1.0
        rather than report >100%."""
        events = [_playbook_start("2026-04-20T10:00:00Z")]
        for task_idx in range(4):
            tid = f"t{task_idx}"
            events.append(_task_start(f"2026-04-20T10:00:{task_idx:02d}Z", task_id=tid))
            for h in ("h1", "h2", "h3"):
                events.append(
                    _runner_ok(f"2026-04-20T10:00:{task_idx + 10:02d}Z", h, task_id=tid)
                )
        events.append(_stats("2026-04-20T10:00:05Z"))
        result = analyze_overhead(events)
        assert result.overhead_share == 1.0


class TestNonStrictTimestamps:
    def test_skips_events_without_timestamp(self) -> None:
        events = [
            _task_start("2026-04-20T10:00:00Z", task_id="t1"),
            {"_event": "v2_runner_on_ok", "task": {"id": "t1"}, "hosts": {"h1": {}}},
            _runner_ok("2026-04-20T10:00:01Z", "h2", task_id="t1"),
        ]
        result = analyze_overhead(events)
        assert result.samples == 1

    def test_skips_negative_durations(self) -> None:
        """Out-of-order timestamps (clock skew, replay artifacts)
        shouldn't contribute negative durations."""
        events = [
            _task_start("2026-04-20T10:00:05Z", task_id="t1"),
            _runner_ok("2026-04-20T10:00:01Z", "h1", task_id="t1"),
        ]
        result = analyze_overhead(events)
        assert result.samples == 0


class TestDataclassShape:
    def test_overhead_stats_is_frozen(self) -> None:
        stats = OverheadStats(
            samples=0,
            distinct_tasks=0,
            distinct_hosts=0,
            overhead_floor_s=None,
            median_duration_s=None,
            wall_clock_s=None,
            estimated_overhead_wall_s=None,
            overhead_share=None,
        )
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            stats.samples = 99
