"""Pure history lookup: find the most recent prior run matching a config + host count.

This module is the "memory" piece of the run-estimate feature. Each
completed session writes its preflight task count + host count into
``meta.json`` (see :func:`ansible_aom.session.store.SessionManager.end_session`);
on a subsequent run the runner asks this module "is there a previous
completed run with the same configuration and host count?". If yes,
the renderer surfaces "Last run: N tasks in T (D ago)" above the
preflight summary.

The function reads ``meta.json`` files directly (so it does I/O) but
holds no other state. It lives in ``session/`` alongside the on-disk
storage layer rather than in pure ``core/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

from ansible_aom.core.run_config import RunConfigKey, build_run_config_key


@dataclass(frozen=True)
class PriorRun:
    """Stats from the most recent matching prior session."""

    session_id: str
    duration_seconds: float
    task_count: int
    host_count: int
    end_time: datetime
    # Loop item totals mined from this session's recorded aggregate
    # events: ``{task.path: {host: item_count}}``. Lets a re-run show a
    # live ``N/total`` loop count. Empty for sessions recorded before
    # event capture, or whose tasks had no loops.
    loop_totals: dict[str, dict[str, int]] = field(default_factory=dict)
    # Per-task wall-clock profile for the live ETA: ``{task.path:
    # per_occurrence_avg_seconds}`` plus the sum of every mined inter-task
    # delta. Both empty / 0.0 for sessions recorded before event capture —
    # the renderer then shows no estimate. See :mod:`ansible_aom.core.estimate`.
    task_wall_s: dict[str, float] = field(default_factory=dict)
    prior_wall_total_s: float = 0.0


def _mine_loop_totals(session_path: Path) -> dict[str, dict[str, int]]:
    """Mine ``{task.path: {host: item_count}}`` from a session's events.

    Scans ``events.jsonl`` for aggregate terminal events
    (``v2_runner_on_ok`` / ``v2_runner_on_failed``) whose per-host result
    carries a non-empty ``results`` array — the signature of a loop — and
    records the loop length per task path per host. Best-effort: a missing
    or malformed events file yields an empty mapping (the live run falls
    back to a bare running count).
    """
    events_file = session_path / "events.jsonl"
    if not events_file.is_file():
        return {}
    totals: dict[str, dict[str, int]] = {}
    try:
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("_event") not in ("v2_runner_on_ok", "v2_runner_on_failed"):
                    continue
                path = event.get("task", {}).get("path")
                if not path:
                    continue
                for host, result in event.get("hosts", {}).items():
                    if not isinstance(result, dict):
                        continue
                    results = result.get("results")
                    if isinstance(results, list) and results:
                        totals.setdefault(path, {})[host] = len(results)
    except OSError:
        return {}
    return totals


def _mine_task_wall(session_path: Path) -> tuple[dict[str, float], float]:
    """Mine ``({task.path: per_occurrence_avg_s}, total_s)`` from a session.

    A task's wall duration is the gap between its ``v2_playbook_on_task_start``
    and the *next* task start (or ``v2_playbook_on_stats`` for the final
    task) — true wall time, including fork/parallelism/overhead, which is
    what the live ETA projects against. A recurring path (role/include run
    twice) accumulates total + count and is exposed as the per-occurrence
    average; the returned total is the full sum of every delta.

    Best-effort: a missing/malformed events file, an unparseable timestamp,
    or a start event lacking a path drops only the affected delta and yields
    an empty profile in the worst case (the renderer shows no estimate).
    """
    events_file = session_path / "events.jsonl"
    if not events_file.is_file():
        return {}, 0.0
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    prev_path: str | None = None
    prev_ts: datetime | None = None
    grand_total = 0.0

    def _close(path: str | None, start: datetime | None, end: datetime | None) -> None:
        nonlocal grand_total
        if path is None or start is None or end is None:
            return
        delta = (end - start).total_seconds()
        if delta < 0:
            return
        totals[path] = totals.get(path, 0.0) + delta
        counts[path] = counts.get(path, 0) + 1
        grand_total += delta

    try:
        with open(events_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = event.get("_event")
                if kind not in ("v2_playbook_on_task_start", "v2_playbook_on_stats"):
                    continue
                ts = _parse_iso(event.get("_timestamp"))
                if kind == "v2_playbook_on_task_start":
                    _close(prev_path, prev_ts, ts)
                    prev_path = event.get("task", {}).get("path")
                    prev_ts = ts
                else:  # v2_playbook_on_stats — close the final task
                    _close(prev_path, prev_ts, ts)
                    prev_path = None
                    prev_ts = None
    except OSError:
        return {}, 0.0

    averages = {path: totals[path] / counts[path] for path in totals}
    return averages, grand_total


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_previous_run(
    session_dir: Path,
    key: RunConfigKey,
    host_count: int,
) -> PriorRun | None:
    """Return the most recent completed session matching ``(key, host_count)``.

    Iterates session directories under ``session_dir``, parses each
    ``meta.json``, and keeps the newest entry that:

    - has ``status == "completed"`` (failed / crashed / running runs
      are unreliable estimates),
    - has a parseable ``end_time``,
    - has all of ``preflight_task_count``, ``resolved_host_count``,
      and ``duration_seconds`` populated (pre-1.2 sessions lack the
      new fields and are skipped),
    - matches ``key`` exactly (rebuilt from the persisted
      ``playbook`` + ``ansible_args``), and
    - has ``resolved_host_count == host_count``.

    Args:
        session_dir: Directory containing per-session subdirectories.
        key: The :class:`RunConfigKey` for the current invocation.
        host_count: Resolved host count for the current invocation
            (union of ``resolved_hosts`` across all preflight plays).

    Returns:
        A :class:`PriorRun` for the most recent match, or ``None`` if
        none of the sessions qualify (including when ``session_dir``
        does not exist).
    """
    if not session_dir.is_dir():
        # Includes both "doesn't exist" and "exists but is a file" — a
        # broken/blocker path on disk shouldn't crash the startup hint
        # lookup.
        return None

    best: tuple[datetime, PriorRun, Path] | None = None

    for entry in session_dir.iterdir():
        if not entry.is_dir():
            continue
        meta_file = entry / "meta.json"
        if not meta_file.exists():
            continue

        try:
            with open(meta_file) as f:
                meta = json.load(f)
        except json.JSONDecodeError, OSError:
            continue

        if meta.get("status") != "completed":
            continue

        task_count = meta.get("preflight_task_count")
        resolved_host_count = meta.get("resolved_host_count")
        duration = meta.get("duration_seconds")
        if task_count is None or resolved_host_count is None or duration is None:
            continue
        if resolved_host_count != host_count:
            continue

        end_time = _parse_iso(meta.get("end_time"))
        if end_time is None:
            continue

        candidate_key = build_run_config_key(
            playbook=meta.get("playbook", ""),
            ansible_args=list(meta.get("ansible_args", [])),
        )
        if candidate_key != key:
            continue

        candidate = PriorRun(
            session_id=meta.get("session_id", entry.name),
            duration_seconds=float(duration),
            task_count=int(task_count),
            host_count=int(resolved_host_count),
            end_time=end_time,
        )
        if best is None or end_time > best[0]:
            best = (end_time, candidate, entry)

    if best is None:
        return None
    # Mine loop totals + the per-task wall profile only for the winning
    # session — reading every session's events.jsonl just to discard all
    # but one would be wasteful.
    task_wall_s, prior_wall_total_s = _mine_task_wall(best[2])
    return replace(
        best[1],
        loop_totals=_mine_loop_totals(best[2]),
        task_wall_s=task_wall_s,
        prior_wall_total_s=prior_wall_total_s,
    )
