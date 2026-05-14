"""Per-task overhead analysis from JSONL event streams.

Why this exists
---------------
Ansible pays a per-task setup cost on every host: fork, exec Python on
the target, ship the module payload, import it, run, serialize result,
ship back. Even with ``-c local`` this floor is ~50–200 ms per task per
host. On runs with many short tasks (debug, set_fact, ping, small
shell), that setup tax can dominate wall-clock.

This module computes a defensible estimate of that overhead from a
recorded session's events. The approach:

1. For each ``(host, task)`` pair, measure the wall-clock duration
   between the task's ``v2_playbook_on_task_start`` and the matching
   ``v2_runner_on_*`` event for that host.
2. Take the 25th percentile of those durations as the "overhead floor"
   — the assumption being that at least a quarter of tasks have
   near-trivial work bodies, so their measured duration is mostly setup.
3. Multiply the floor by the distinct-task count (not host-task count,
   because ansible parallelizes hosts up to ``forks``) to estimate the
   wall-clock time spent on setup.

This is a heuristic, not a measurement. The display layer should frame
it as approximate.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Need this many host-task duration samples before P25 is meaningful.
# Below this we report sample count but no percentile.
_MIN_SAMPLES_FOR_P25 = 4

_RUNNER_RESULT_EVENTS = frozenset(
    {
        "v2_runner_on_ok",
        "v2_runner_on_failed",
        "v2_runner_on_unreachable",
        "v2_runner_on_skipped",
    }
)


@dataclass(frozen=True)
class OverheadStats:
    """Per-task overhead summary.

    ``None`` fields signal "insufficient data": either no samples at all
    or fewer than the P25 minimum. Display layers should handle the
    ``None`` case explicitly rather than substituting zero.
    """

    samples: int
    distinct_tasks: int
    distinct_hosts: int
    overhead_floor_s: float | None
    median_duration_s: float | None
    wall_clock_s: float | None
    estimated_overhead_wall_s: float | None
    overhead_share: float | None


def analyze_overhead(events: list[dict[str, Any]]) -> OverheadStats:
    """Return the overhead summary for a recorded session's events.

    Args:
        events: JSONL events as produced by ``ansible.posix.jsonl``.

    Returns:
        ``OverheadStats``. With no measurable samples, percentile and
        share fields are ``None``; with samples but below the P25
        threshold, only the percentile/share fields are ``None``.
    """
    task_starts: dict[str, datetime] = {}
    durations: list[float] = []
    distinct_hosts: set[str] = set()

    pb_start: datetime | None = None
    pb_end: datetime | None = None

    for event in events:
        kind = event.get("_event")
        ts_raw = event.get("_timestamp")
        ts = _parse_iso8601(ts_raw) if ts_raw else None

        if kind == "v2_playbook_on_start" and ts is not None:
            pb_start = ts
            continue
        if kind == "v2_playbook_on_stats" and ts is not None:
            pb_end = ts
            continue
        if kind == "v2_playbook_on_task_start" and ts is not None:
            task_id = event.get("task", {}).get("id")
            if task_id:
                task_starts[task_id] = ts
            continue
        if kind in _RUNNER_RESULT_EVENTS and ts is not None:
            task_id = event.get("task", {}).get("id")
            if not task_id or task_id not in task_starts:
                continue
            duration = (ts - task_starts[task_id]).total_seconds()
            if duration < 0:
                continue
            hosts = event.get("hosts") or {}
            for host in hosts:
                durations.append(duration)
                distinct_hosts.add(host)

    samples = len(durations)
    wall_clock = (pb_end - pb_start).total_seconds() if pb_start and pb_end else None

    if samples < _MIN_SAMPLES_FOR_P25:
        return OverheadStats(
            samples=samples,
            distinct_tasks=len(task_starts),
            distinct_hosts=len(distinct_hosts),
            overhead_floor_s=None,
            median_duration_s=None,
            wall_clock_s=wall_clock,
            estimated_overhead_wall_s=None,
            overhead_share=None,
        )

    floor = _quantile(durations, 0.25)
    median = statistics.median(durations)
    distinct_tasks = len(task_starts)
    est_wall = floor * distinct_tasks

    share: float | None = None
    if wall_clock is not None and wall_clock > 0:
        share = min(est_wall / wall_clock, 1.0)

    return OverheadStats(
        samples=samples,
        distinct_tasks=distinct_tasks,
        distinct_hosts=len(distinct_hosts),
        overhead_floor_s=floor,
        median_duration_s=median,
        wall_clock_s=wall_clock,
        estimated_overhead_wall_s=est_wall,
        overhead_share=share,
    )


def _parse_iso8601(ts: str) -> datetime | None:
    """Parse the ISO-8601 timestamps emitted by ansible.posix.jsonl.

    Returns ``None`` for malformed input rather than raising — overhead
    analysis is best-effort; one bad timestamp shouldn't poison the run.
    """
    try:
        # Python's fromisoformat accepts "Z" suffix since 3.11.
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _quantile(values: list[float], q: float) -> float:
    """Linear-interpolation quantile (matches numpy's default).

    Hand-rolled so we don't depend on numpy for one call. ``q`` in [0, 1].
    """
    if not values:
        raise ValueError("quantile of empty list")
    sorted_v = sorted(values)
    if len(sorted_v) == 1:
        return sorted_v[0]
    pos = q * (len(sorted_v) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_v) - 1)
    frac = pos - lo
    return sorted_v[lo] + frac * (sorted_v[hi] - sorted_v[lo])
