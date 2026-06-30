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
``AOM_DEBUG``      — turn on every verbose diagnostic in one knob:
                     DEBUG-level logging on ``ansible_aom``, per-loop
                     pexpect trace, every-100th-event stderr counter,
                     and the post-run ``[aom-debug]`` summary on
                     stderr. Lifecycle marks are *always* recorded
                     (one bool check + a small list); this flag
                     decides whether the summary is *printed*.
``AOM_PROFILE``    — wrap ``_drive`` in ``cProfile`` and dump pstats
                     to ``~/.local/state/aom/profile/<sid>.pstats``.
                     ~5-10% CPU cost; separate because it writes a
                     distinct artifact.
``AOM_TRACEMALLOC``— start ``tracemalloc``; record the peak in
                     ``diagnostics.json``. ~10% memory cost.
``AOM_WATCHDOG``   — integer seconds; arms
                     ``faulthandler.dump_traceback_later`` with
                     ``repeat=True``. Catches hangs without a fault.

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
import sys
import time
import tracemalloc
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any

_LOGGER_NAME = "ansible_aom"

# Module-level state. Reset only via _reset_for_testing.
_installed: bool = False
_debug: bool = False
_watchdog_seconds: int | None = None
_lifecycle_marks: list[tuple[str, int]] = []
_profile_enabled: bool = False
_tracemalloc_enabled: bool = False
_profiler: cProfile.Profile | None = None
_tracemalloc_peak_kb: int | None = None
_session_recording_disabled: bool = False
_session_disable_reason: str | None = None
_psutil_disabled_reason: str | None = None


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

    - ``AOM_DEBUG``      → DEBUG logger + pexpect trace + events trace
                          + post-run stderr summary (one knob).
    - ``AOM_WATCHDOG``   → calls ``faulthandler.dump_traceback_later``.
    - ``AOM_PROFILE``    → creates a ``cProfile.Profile``.
    - ``AOM_TRACEMALLOC``→ ``tracemalloc.start()``.
    """
    global _installed, _debug, _watchdog_seconds
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
    global _installed, _debug, _watchdog_seconds
    global _last_run_diagnostics, _last_renderer_stats
    global _profile_enabled, _tracemalloc_enabled, _profiler, _tracemalloc_peak_kb
    global _session_recording_disabled, _session_disable_reason
    global _psutil_disabled_reason
    if _watchdog_seconds is not None:
        try:
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    _installed = False
    _debug = False
    _watchdog_seconds = None
    _lifecycle_marks.clear()
    _last_run_diagnostics = None
    _last_renderer_stats = None
    _profile_enabled = False
    _tracemalloc_enabled = False
    _profiler = None
    _tracemalloc_peak_kb = None
    _session_recording_disabled = False
    _session_disable_reason = None
    _psutil_disabled_reason = None


def is_debug() -> bool:
    return _debug


def set_debug(enable: bool = True) -> None:
    """Enable/disable debug mode programmatically.

    Called by cli.py when the --verbose flag is passed.
    Can also be called from tests to avoid env-var coupling.
    Idempotent — safe to call even after install_from_env().
    """
    global _debug
    _debug = enable
    if enable:
        logging.getLogger(_LOGGER_NAME).setLevel(logging.DEBUG)


def watchdog_seconds() -> int | None:
    return _watchdog_seconds


def lifecycle_mark(name: str) -> None:
    """Record a named timestamp (monotonic nanoseconds).

    Always-on: the cost is one ``time.monotonic_ns`` syscall plus a
    list append, total ~100 ns. Lifecycle marks always flow into
    ``diagnostics.json`` so post-mortem has the timeline regardless
    of whether ``AOM_DEBUG`` was set at run time. ``AOM_DEBUG`` only
    controls whether the post-run summary is *printed*.
    """
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
    preflight_ms: int = 0
    event_histogram: dict[str, int] = field(default_factory=dict)
    _first_event_marked: bool = False

    def note_preflight_elapsed_ms(self, ms: int) -> None:
        """Record total preflight elapsed time (parallel list-tasks + list-hosts)."""
        self.preflight_ms = ms

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


def set_session_recording_disabled(reason: str) -> None:
    """Flag that session recording was disabled mid-run with ``reason``.

    Called by :class:`ansible_aom.ansible.runner._SessionSink` when a
    write OSError forced it to give up. The flag + reason are surfaced
    in ``diagnostics.json`` so post-mortem can tell "recording stopped
    here" from "recording never started".
    """
    global _session_recording_disabled, _session_disable_reason
    _session_recording_disabled = True
    _session_disable_reason = reason


def session_recording_disabled() -> bool:
    return _session_recording_disabled


def session_disable_reason() -> str | None:
    return _session_disable_reason


def set_psutil_disabled(reason: str) -> None:
    """Flag that psutil-based CPU sampling was disabled with ``reason``.

    Set by :func:`ansible_aom.ansible.runner._sample_subprocess_active`
    when its subprocess-probe of ``import psutil`` exits non-zero (which
    happens when the C extension's shared object is ABI-incompatible with
    the running interpreter — e.g. uv-installed CPython trying to load a
    Nix-built ``_psutil_linux.abi3.so``). The flag is surfaced in the
    post-run summary so users see *why* their CPU heartbeat went silent.
    """
    global _psutil_disabled_reason
    _psutil_disabled_reason = reason


def psutil_disabled_reason() -> str | None:
    return _psutil_disabled_reason


def print_summary_if_debug(file: IO[str] | None = None) -> None:
    """Emit a single-line ``[aom-debug] …`` post-run digest to ``file``.

    Silent unless ``AOM_DEBUG=1`` or the ``--verbose`` CLI flag is passed.
    Reads from the in-process
    accumulators (``get_last_run_diagnostics`` / ``get_last_renderer_stats``)
    plus the top-N event histogram entries, so the user doesn't have
    to chase ``aom inspect --debug`` to see the post-run signal that
    matters most.

    ``file`` defaults to ``sys.stderr`` so the summary doesn't pollute
    the renderer's stdout (json/jq pipelines, capture-on-success
    workflows).
    """
    if not _debug:
        return
    out = file if file is not None else sys.stderr

    diag = _last_run_diagnostics
    stats = _last_renderer_stats
    if diag is None and stats is None:
        out.write("[aom-debug] no run data published (early exit / no playbook run)\n")
        return

    events = diag.events_received if diag is not None else 0
    pty_bytes = diag.pty_bytes if diag is not None else 0
    timeouts = diag.pexpect_timeouts if diag is not None else 0
    stall_max = diag.stall_count_max if diag is not None else 0
    preflight = diag.preflight_ms if diag is not None else 0

    renders = stats.render_calls if stats is not None else 0
    log_writes = stats.log_writes if stats is not None else 0

    top: list[str] = []
    if diag is not None and diag.event_histogram:
        items = sorted(diag.event_histogram.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        top = [f"{name}×{count}" for name, count in items]

    parts = [
        f"events={events}",
        f"renders={renders}",
        f"log_writes={log_writes}",
        f"pty_bytes={pty_bytes}",
        f"pexpect_timeouts={timeouts}",
        f"stall_max={stall_max}",
        f"preflight_ms={preflight}",
    ]
    if top:
        parts.append("top=" + ",".join(top))
    if _tracemalloc_peak_kb is not None:
        parts.append(f"tracemalloc_peak_kb={_tracemalloc_peak_kb}")
    if _session_recording_disabled:
        parts.append(f"recording_disabled={_session_disable_reason!r}")
    if _psutil_disabled_reason is not None:
        parts.append(f"psutil_disabled={_psutil_disabled_reason!r}")

    out.write("[aom-debug] " + " ".join(parts) + "\n")


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
    preflight_ms: int = 0
    state_size_bytes: int | None = None
    max_rss_kb: int | None = None
    tracemalloc_peak_kb: int | None = None


SCHEMA_VERSION = 1

# Render-storm heuristic. Triggered when render_calls / events_received
# is implausibly large — i.e. the renderer is doing redundant work the
# user is unlikely to see. Threshold chosen so a 5 Hz panel refresh
# during a fast run (50ms tasks) doesn't trip the warning; pathological
# cases (per-host per-event redraws) blow past 10x easily.
_RENDER_STORM_RATIO_THRESHOLD = 5.0
_RENDER_STORM_MIN_EVENTS = 50


def render_storm_warning(stats: RendererStats) -> str | None:
    """Detect render-call inflation vs. event rate.

    Returns a one-line warning when the renderer is redrawing far more
    often than the runner emits events; ``None`` otherwise (including
    short runs where the ratio is statistically noise).
    """
    if stats.events_received < _RENDER_STORM_MIN_EVENTS:
        return None
    ratio = stats.render_calls / stats.events_received
    if ratio < _RENDER_STORM_RATIO_THRESHOLD:
        return None
    return (
        f"render-storm detected: {stats.render_calls} panel renders for "
        f"{stats.events_received} events (ratio {ratio:.1f}× — see "
        f"docs/superpowers/specs/2026-05-21-render-state-perf-design.md "
        f"HS-1 / HS-8)."
    )


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
    psutil_disabled_reason: str | None = None,
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
        "preflight_ms": stats.preflight_ms,
        "session_recording_disabled": session_recording_disabled,
        "session_disable_reason": session_disable_reason,
        "psutil_disabled_reason": psutil_disabled_reason,
    }

    resources: dict[str, Any] = {
        "max_rss_kb": stats.max_rss_kb,
        "state_size_bytes": stats.state_size_bytes,
        "tracemalloc_peak_kb": stats.tracemalloc_peak_kb,
    }

    warnings: list[str] = []
    storm = render_storm_warning(stats)
    if storm is not None:
        warnings.append(storm)

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
        "warnings": warnings,
    }
