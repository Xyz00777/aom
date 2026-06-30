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
from typing import Any

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
    # Result-segmented profile: ``variable_paths`` are the task paths whose
    # prior result was ``changed`` (or failed/unreachable) — the variable
    # work — and ``prior_var_total_s`` is the wall those paths account for.
    # The rest is the fixed (ok/skipped) floor. Used to scale only the
    # variable part of the ETA. See :mod:`ansible_aom.core.estimate`.
    variable_paths: frozenset[str] = field(default_factory=frozenset)
    prior_var_total_s: float = 0.0


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


def _mine_task_wall(
    session_path: Path,
) -> tuple[dict[str, float], float, frozenset[str], float]:
    """Mine the per-task wall profile + result segmentation from a session.

    Returns ``(averages, total_s, variable_paths, variable_total_s)``:

    - ``averages`` maps ``task.path`` to its per-occurrence average wall, the
      gap between its ``v2_playbook_on_task_start`` and the *next* task start
      (or ``v2_playbook_on_stats`` for the final task) — true wall time,
      including fork/parallelism/overhead. A recurring path accumulates and is
      exposed as the average; ``total_s`` is the full sum of every delta.
    - ``variable_paths`` are the paths whose terminal result was ``changed``
      (any host) or failed/unreachable — the variable work. Paths seen only
      as ``ok``-without-change or ``skipped`` stay in the fixed floor.
    - ``variable_total_s`` is the wall those variable paths account for.

    Best-effort: a missing/malformed events file, an unparseable timestamp,
    or a start event lacking a path drops only the affected datum and yields
    an empty profile in the worst case (the renderer shows no estimate).
    """
    events_file = session_path / "events.jsonl"
    if not events_file.is_file():
        return {}, 0.0, frozenset(), 0.0
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    variable: set[str] = set()
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
                if kind == "v2_playbook_on_task_start":
                    ts = _parse_iso(event.get("_timestamp"))
                    _close(prev_path, prev_ts, ts)
                    prev_path = event.get("task", {}).get("path")
                    prev_ts = ts
                elif kind == "v2_playbook_on_stats":
                    _close(prev_path, prev_ts, _parse_iso(event.get("_timestamp")))
                    prev_path = None
                    prev_ts = None
                elif kind in ("v2_runner_on_failed", "v2_runner_on_unreachable"):
                    path = event.get("task", {}).get("path")
                    if path:
                        variable.add(path)
                elif kind == "v2_runner_on_ok":
                    path = event.get("task", {}).get("path")
                    if path and any(
                        isinstance(h, dict) and h.get("changed")
                        for h in event.get("hosts", {}).values()
                    ):
                        variable.add(path)
    except OSError:
        return {}, 0.0, frozenset(), 0.0

    averages = {path: totals[path] / counts[path] for path in totals}
    variable_total = sum(totals[path] for path in variable if path in totals)
    return averages, grand_total, frozenset(variable), variable_total


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iter_completed_sessions(
    session_dir: Path,
) -> list[tuple[datetime, dict[str, Any], Path]]:
    """Yield ``(end_time, meta, session_path)`` for every valid completed session.

    Filters out sessions whose ``meta.json`` is missing or malformed,
    whose status is not ``completed``, or whose required fields
    (``preflight_task_count``, ``resolved_host_count``, ``duration_seconds``,
    ``end_time``) are absent. The result is sorted newest-first by
    ``end_time``.
    """
    if not session_dir.is_dir():
        return []
    result: list[tuple[datetime, dict[str, Any], Path]] = []
    for entry in session_dir.iterdir():
        if not entry.is_dir():
            continue
        meta_file = entry / "meta.json"
        if not meta_file.exists():
            continue
        try:
            with open(meta_file) as f:
                meta: dict[str, Any] = json.load(f)
        except json.JSONDecodeError, OSError:
            continue
        if meta.get("status") != "completed":
            continue
        task_count = meta.get("preflight_task_count")
        host_count_val = meta.get("resolved_host_count")
        duration = meta.get("duration_seconds")
        if task_count is None or host_count_val is None or duration is None:
            continue
        end_time = _parse_iso(meta.get("end_time"))
        if end_time is None:
            continue
        result.append((end_time, meta, entry))
    result.sort(key=lambda x: x[0], reverse=True)
    return result


def _match_strict(meta: dict[str, Any], key: RunConfigKey, host_count: int) -> bool:
    """True when the stored session matches the current invocation exactly."""
    if meta.get("resolved_host_count") != host_count:
        return False
    candidate_key = build_run_config_key(
        playbook=meta.get("playbook", ""),
        ansible_args=list(meta.get("ansible_args", [])),
    )
    return candidate_key == key


def _match_loose(meta: dict[str, Any], key: RunConfigKey, host_count: int) -> bool:
    """True when the stored session matches the current invocation loosely.

    Loose matching compares only the resolved playbook path and the host
    count — tags, limit, extra vars, and other run-config flags are
    intentionally ignored. This gives the user a useful prior even when
    they vary flags between runs (different ``--tags``, ``--diff`` on/off,
    etc.).
    """
    if meta.get("resolved_host_count") != host_count:
        return False
    stored_playbook = meta.get("playbook", "")
    if not isinstance(stored_playbook, str):
        return False
    return str(Path(stored_playbook).resolve()) == key.playbook


def _build_prior(meta: dict[str, Any], entry: Path, end_time: datetime) -> PriorRun:
    return PriorRun(
        session_id=str(meta.get("session_id", entry.name)),
        duration_seconds=float(meta["duration_seconds"]),
        task_count=int(meta["preflight_task_count"]),
        host_count=int(meta["resolved_host_count"]),
        end_time=end_time,
    )


def _mine_and_replace(prior: PriorRun, session_path: Path) -> PriorRun:
    """Mine per-task wall and loop totals for *prior*, returning a new PriorRun."""
    task_wall_s, prior_wall_total_s, variable_paths, prior_var_total_s = _mine_task_wall(
        session_path
    )
    return replace(
        prior,
        loop_totals=_mine_loop_totals(session_path),
        task_wall_s=task_wall_s,
        prior_wall_total_s=prior_wall_total_s,
        variable_paths=variable_paths,
        prior_var_total_s=prior_var_total_s,
    )


def find_previous_run(
    session_dir: Path,
    key: RunConfigKey,
    host_count: int,
) -> PriorRun | None:
    """Return the most recent completed session matching ``(key, host_count)``.

    Two-pass matching:

    1. **Strict** — the stored ``RunConfigKey`` (rebuilt from persisted
       ``playbook`` + ``ansible_args``) must equal *key* exactly, **and**
       the stored ``resolved_host_count`` must equal *host_count*.
    2. **Loose** (fallback) — only the resolved playbook path and host
       count must match. Tags, limit, extra vars, and other run-config
       flags are ignored. This gives the user a useful prior even when
       they vary flags between runs.

    Both passes exclude sessions that are not ``completed``, missing
    required fields, or pre-1.2 format.

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
    candidates = _iter_completed_sessions(session_dir)
    if not candidates:
        return None

    for end_time, meta, entry in candidates:
        if _match_strict(meta, key, host_count):
            return _mine_and_replace(_build_prior(meta, entry, end_time), entry)

    for end_time, meta, entry in candidates:
        if _match_loose(meta, key, host_count):
            return _mine_and_replace(_build_prior(meta, entry, end_time), entry)

    return None
