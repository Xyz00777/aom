"""Opt-in diagnostics / observability layer for AOM.

Pure module — reads ``os.environ``, calls a small set of stdlib facilities
(``faulthandler``, ``logging``, ``time.monotonic_ns``) and exposes flags +
helpers other layers consult. No imports from ``compact``, ``tui``,
``renderer``, ``ansible``, ``session``, ``drivers``, ``inspect``, or
``rerun`` — those layers call *into* this module.

Phase 1 of the diagnostics-layer plan
(``docs/superpowers/specs/2026-05-21-diagnostics-layer-design.md``):
flag plumbing, ``install_from_env``, lifecycle marks, and the pure
``build_diagnostics_record`` value-builder. No call sites yet — wiring
happens in later phases.

Env vars
--------
``AOM_DEBUG``           — enable DEBUG logging on the ``ansible_aom``
                          logger and record lifecycle marks.
``AOM_TRACE_PEXPECT``   — enable per-loop pexpect trace (replaces the
                          legacy ``AOM_TRACE``).
``AOM_TRACE``           — legacy alias for ``AOM_TRACE_PEXPECT``.
``AOM_TRACE_EVENTS``    — log every Nth JSONL event with running counters.
``AOM_WATCHDOG``        — integer seconds; arms
                          ``faulthandler.dump_traceback_later`` with
                          ``repeat=True``. Zero/invalid disables.

Falsy values
------------
``"0"`` and ``""`` count as "off" for any boolean flag. Anything else
counts as "on". This matches how shell-set env vars are typically read.

Idempotence
-----------
``install_from_env`` is idempotent — the first call wins; later calls
return immediately. Tests call ``_reset_for_testing()`` to clear state.
"""

from __future__ import annotations

import faulthandler
import logging
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_LOGGER_NAME = "ansible_aom"

# Module-level state. Reset only via _reset_for_testing.
_installed: bool = False
_debug: bool = False
_trace_pexpect: bool = False
_trace_events: bool = False
_watchdog_seconds: int | None = None
_lifecycle_marks: list[tuple[str, int]] = []


def _is_truthy(value: str | None) -> bool:
    """Return True iff ``value`` is set and not a known falsy literal."""
    if value is None:
        return False
    return value not in ("", "0")


def _parse_watchdog(value: str | None) -> int | None:
    """Parse ``AOM_WATCHDOG`` into a positive int, else None."""
    if value is None or value == "":
        return None
    try:
        seconds = int(value)
    except ValueError:
        return None
    if seconds <= 0:
        return None
    return seconds


def install_from_env(env: Mapping[str, str] | None = None) -> None:
    """Install diagnostics based on ``env`` (defaults to ``os.environ``).

    Idempotent: the first call latches the configuration; subsequent
    calls return immediately. Always enables ``faulthandler`` —
    that single syscall is cheap and is the single most useful signal
    for "AOM died in native code" reports.

    Side effects (per env var):

    - ``AOM_DEBUG``         → sets the ``ansible_aom`` logger to DEBUG.
    - ``AOM_WATCHDOG``      → calls ``faulthandler.dump_traceback_later``.
    - ``AOM_TRACE_PEXPECT`` → flips :func:`is_trace_pexpect` to True.
    - ``AOM_TRACE``         → alias for ``AOM_TRACE_PEXPECT``.
    - ``AOM_TRACE_EVENTS``  → flips :func:`is_trace_events` to True.
    """
    global _installed, _debug, _trace_pexpect, _trace_events, _watchdog_seconds

    if _installed:
        return
    _installed = True

    source = env if env is not None else os.environ

    # faulthandler is unconditional: zero cost when off, single most
    # useful signal when it fires.
    if not faulthandler.is_enabled():
        faulthandler.enable()

    _debug = _is_truthy(source.get("AOM_DEBUG"))
    _trace_pexpect = _is_truthy(source.get("AOM_TRACE_PEXPECT")) or _is_truthy(
        source.get("AOM_TRACE")
    )
    _trace_events = _is_truthy(source.get("AOM_TRACE_EVENTS"))
    _watchdog_seconds = _parse_watchdog(source.get("AOM_WATCHDOG"))

    if _debug:
        logging.getLogger(_LOGGER_NAME).setLevel(logging.DEBUG)

    if _watchdog_seconds is not None:
        # ``repeat=True`` so a long-running stuck process keeps producing
        # stacks (every N seconds), not just one dump.
        faulthandler.dump_traceback_later(_watchdog_seconds, repeat=True)


def _reset_for_testing() -> None:
    """Test-only: undo all module state so each test gets a fresh install.

    Cancels the watchdog timer if armed, but does NOT disable
    ``faulthandler`` — leaving it on between tests is safe and matches
    production behavior (where it stays on for the process lifetime).
    """
    global _installed, _debug, _trace_pexpect, _trace_events, _watchdog_seconds
    if _watchdog_seconds is not None:
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
    _installed = False
    _debug = False
    _trace_pexpect = False
    _trace_events = False
    _watchdog_seconds = None
    _lifecycle_marks.clear()


def is_debug() -> bool:
    return _debug


def is_trace_pexpect() -> bool:
    return _trace_pexpect


def is_trace_events() -> bool:
    return _trace_events


def watchdog_seconds() -> int | None:
    return _watchdog_seconds


def lifecycle_mark(name: str) -> None:
    """Record a named timestamp (monotonic nanoseconds) when debug is on.

    No-op when ``AOM_DEBUG`` is unset, so the call site cost in steady
    state is one bool check.
    """
    if not _debug:
        return
    _lifecycle_marks.append((name, time.monotonic_ns()))


def get_lifecycle_marks() -> list[tuple[str, int]]:
    """Return a *copy* of the recorded lifecycle marks (name, monotonic_ns)."""
    return list(_lifecycle_marks)


@dataclass(frozen=True)
class RendererStats:
    """Counters collected by the renderer over a run.

    Phase 1 carries the bare fields; phases 3-4 wire the increment sites
    in ``ansible/runner.py`` and ``compact/renderer.py``.
    """

    events_received: int = 0
    render_calls: int = 0
    log_writes: int = 0
    pty_bytes: int = 0
    stall_count_max: int = 0
    pexpect_timeouts: int = 0
    state_size_bytes: int | None = None
    max_rss_kb: int | None = None
    tracemalloc_peak_kb: int | None = None


SCHEMA_VERSION = 1


def build_diagnostics_record(
    *,
    session_id: str,
    aom_version: str,
    lifecycle_marks_ns: list[tuple[str, int]],
    stats: RendererStats,
    event_histogram: Mapping[str, int],
    env_snapshot: Mapping[str, str],
    host_count: int | None = None,
    playbook_task_count: int | None = None,
    session_recording_disabled: bool = False,
    session_disable_reason: str | None = None,
) -> dict[str, Any]:
    """Build the JSON-serializable ``diagnostics.json`` payload.

    Pure: no I/O, no clock reads, no env reads. Callers pass everything
    in. The ``lifecycle_marks_ns`` list is converted into a millisecond
    delta dict (anchored at the earliest mark) so consumers don't have
    to know about ``monotonic_ns``. Empty list → empty dict.

    Schema mirrors §5 of the diagnostics design spec.
    """
    lifecycle_ms: dict[str, int] = {}
    if lifecycle_marks_ns:
        anchor_ns = lifecycle_marks_ns[0][1]
        for name, ns in lifecycle_marks_ns:
            lifecycle_ms[f"{name}_ms"] = (ns - anchor_ns) // 1_000_000

    counters: dict[str, Any] = {
        "events_received": stats.events_received,
        "render_calls": stats.render_calls,
        "log_writes": stats.log_writes,
        "pty_bytes": stats.pty_bytes,
        "stall_count_max": stats.stall_count_max,
        "pexpect_timeouts": stats.pexpect_timeouts,
        "session_recording_disabled": session_recording_disabled,
        "session_disable_reason": session_disable_reason,
    }

    resources: dict[str, Any] = {
        "max_rss_kb": stats.max_rss_kb,
        "state_size_bytes": stats.state_size_bytes,
        "tracemalloc_peak_kb": stats.tracemalloc_peak_kb,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        "aom_version": aom_version,
        "lifecycle": lifecycle_ms,
        "counters": counters,
        "resources": resources,
        "event_histogram": dict(event_histogram),
        "env_snapshot": dict(env_snapshot),
        "host_count": host_count,
        "playbook_task_count": playbook_task_count,
    }
