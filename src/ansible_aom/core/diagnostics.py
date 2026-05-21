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

import cProfile
import faulthandler
import logging
import os
import time
import tracemalloc
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOGGER_NAME = "ansible_aom"

# Module-level state. Reset only via _reset_for_testing.
_installed: bool = False
_debug: bool = False
_trace_pexpect: bool = False
_trace_events: bool = False
_watchdog_seconds: int | None = None
_lifecycle_marks: list[tuple[str, int]] = []
_profile_enabled: bool = False
_tracemalloc_enabled: bool = False
_profiler: cProfile.Profile | None = None
_tracemalloc_peak_kb: int | None = None


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
    global _profile_enabled, _tracemalloc_enabled, _profiler

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
    _profile_enabled = _is_truthy(source.get("AOM_PROFILE"))
    _tracemalloc_enabled = _is_truthy(source.get("AOM_TRACEMALLOC"))

    if _debug:
        logging.getLogger(_LOGGER_NAME).setLevel(logging.DEBUG)

    if _watchdog_seconds is not None:
        # ``repeat=True`` so a long-running stuck process keeps producing
        # stacks (every N seconds), not just one dump.
        faulthandler.dump_traceback_later(_watchdog_seconds, repeat=True)

    if _profile_enabled:
        # Created here but not yet enabled — the runner enables it
        # around ``_drive`` so we only profile the hot path, not import
        # bootstrapping or argparse.
        _profiler = cProfile.Profile()

    if _tracemalloc_enabled and not tracemalloc.is_tracing():
        tracemalloc.start()


def _reset_for_testing() -> None:
    """Test-only: undo all module state so each test gets a fresh install.

    Cancels the watchdog timer if armed, but does NOT disable
    ``faulthandler`` — leaving it on between tests is safe and matches
    production behavior (where it stays on for the process lifetime).
    """
    global _installed, _debug, _trace_pexpect, _trace_events, _watchdog_seconds
    global _last_run_diagnostics, _last_renderer_stats
    global _profile_enabled, _tracemalloc_enabled, _profiler, _tracemalloc_peak_kb
    if _watchdog_seconds is not None:
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    _installed = False
    _debug = False
    _trace_pexpect = False
    _trace_events = False
    _watchdog_seconds = None
    _lifecycle_marks.clear()
    _last_run_diagnostics = None
    _last_renderer_stats = None
    _profile_enabled = False
    _tracemalloc_enabled = False
    _profiler = None
    _tracemalloc_peak_kb = None


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


@dataclass
class RunDiagnostics:
    """Mutable per-run accumulator threaded through ``run_playbook``.

    Captures the counters that ``diagnostics.json`` (phase 5) needs and
    fires the ``first_event`` lifecycle mark the first time
    :meth:`note_event` is called. Distinct from :class:`RendererStats`
    (which is the renderer's view of its own activity); the two are
    merged at completion when the JSON record is built.

    Counters increment regardless of ``AOM_DEBUG`` — they're the only
    way to answer "how many events did the run see?" in post-mortem.
    Lifecycle marks remain debug-gated; the counter is the cheap
    always-on signal, the marks are the richer opt-in one.
    """

    events_received: int = 0
    pty_bytes: int = 0
    pexpect_timeouts: int = 0
    stall_count_max: int = 0
    event_histogram: dict[str, int] = field(default_factory=dict)
    _first_event_marked: bool = False

    def note_event(self, event_type: str) -> None:
        if not self._first_event_marked:
            lifecycle_mark("first_event")
            self._first_event_marked = True
        self.events_received += 1
        self.event_histogram[event_type] = self.event_histogram.get(event_type, 0) + 1

    def note_timeout(self) -> None:
        self.pexpect_timeouts += 1

    def note_stall(self, stall_count: int) -> None:
        if stall_count > self.stall_count_max:
            self.stall_count_max = stall_count

    def note_pty_bytes(self, n: int) -> None:
        self.pty_bytes += n


_last_run_diagnostics: RunDiagnostics | None = None
_last_renderer_stats: "RendererStats | None" = None


def set_last_run_diagnostics(diag: RunDiagnostics | None) -> None:
    """Publish the just-finished run's diagnostics for post-hoc readers.

    Phase 5 uses this to plumb the accumulator into ``diagnostics.json``
    without changing :func:`ansible_aom.ansible.runner.run_playbook`'s
    int return signature.
    """
    global _last_run_diagnostics
    _last_run_diagnostics = diag


def get_last_run_diagnostics() -> RunDiagnostics | None:
    return _last_run_diagnostics


def set_last_renderer_stats(stats: "RendererStats | None") -> None:
    """Publish a renderer's final activity snapshot.

    Renderers call this from :py:meth:`stop` so phase 5 can fold the
    counters into ``diagnostics.json`` without a tighter coupling
    between session/store and the renderer.
    """
    global _last_renderer_stats
    _last_renderer_stats = stats


def get_last_renderer_stats() -> "RendererStats | None":
    return _last_renderer_stats


def is_profile() -> bool:
    return _profile_enabled


def is_tracemalloc() -> bool:
    return _tracemalloc_enabled


def get_profiler() -> cProfile.Profile | None:
    """Return the global cProfile instance when ``AOM_PROFILE=1``, else None.

    Callers enable/disable around the section they want to profile.
    Created once in :func:`install_from_env`; the runner enables it
    around ``_drive`` so import-time bootstrap doesn't pollute the
    sample set.
    """
    return _profiler


def dump_profile(target: Path) -> None:
    """Write the cProfile stats to ``target`` in pstats binary format.

    No-op when ``AOM_PROFILE`` is off or the profiler is None.
    """
    if _profiler is None:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _profiler.dump_stats(str(target))


def record_tracemalloc_peak() -> None:
    """Snapshot the current ``tracemalloc`` peak and stash it for later.

    Reads ``tracemalloc.get_traced_memory()[1]`` which is the running
    peak since ``tracemalloc.start()``. Stored as KB rounded down so
    the JSON record stays small. No-op when tracing isn't active.
    """
    global _tracemalloc_peak_kb
    if not _tracemalloc_enabled or not tracemalloc.is_tracing():
        return
    _, peak_bytes = tracemalloc.get_traced_memory()
    _tracemalloc_peak_kb = peak_bytes // 1024


def get_tracemalloc_peak_kb() -> int | None:
    return _tracemalloc_peak_kb


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
