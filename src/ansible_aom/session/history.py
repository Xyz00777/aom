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
from dataclasses import dataclass
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

    best: tuple[datetime, PriorRun] | None = None

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
            best = (end_time, candidate)

    return best[1] if best else None
