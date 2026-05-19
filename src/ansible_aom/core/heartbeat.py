"""Pure liveness state machine for the currently running ansible task.

Distinguishes three states from two facts fed in by the runner:

- ``last_byte_at``  : monotonic timestamp of the most recent PTY byte
- ``cpu_active_at`` : most recent CPU sample that observed activity in
  the subprocess (or its descendants, e.g. ``brew``)

The runner owns the side effects (pexpect reads, psutil sampling) and
calls ``note_bytes`` / ``note_cpu_sample`` to feed timestamps in. This
module stays free of I/O so it can be exercised by injecting plain
floats — see ``tests/unit/test_heartbeat.py``.

State derivation (see ``state``)::

    no bytes ever                     → None
    byte age < live_threshold_s       → LIVE (reason=pty)
    cpu age < live_threshold_s        → LIVE (reason=cpu)  # silent but busy
    byte age < stuck_threshold_s      → WORKING (reason=silent)
    cpu age < stuck_threshold_s       → WORKING (reason=cpu)  # rescued from stuck
    otherwise                         → STUCK (reason=stuck)

The CPU-promotion path matters for tasks that emit no PTY bytes for
long stretches but are clearly doing work — e.g. ``community.general.homebrew``
in a loop, where ansible itself spins up Python module subprocesses
before any ``brew`` output reaches the JSONL channel. Without it the
user sees ○ at 5s and assumes AOM is stuck.

No explicit task-boundary reset is needed: the ``v2_playbook_on_task_start``
line is itself a PTY byte that the runner notes, so the new task's
observation window opens naturally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LivenessLevel = Literal["live", "working", "stuck"]

# ``reason`` annotates the level so the UI can show *why* the dot is the
# colour it is. ``pty`` and ``cpu`` are positive signals; ``silent`` and
# ``stuck`` are absences (no PTY, no recent CPU).
LivenessReason = Literal["pty", "cpu", "silent", "stuck"]

# Defaults chosen so that a brief stutter (network blip, slow brew
# formula) reads as WORKING rather than alarming the user, while a
# truly stalled subprocess still surfaces within half a minute.
_DEFAULT_LIVE_THRESHOLD_S = 5.0
_DEFAULT_STUCK_THRESHOLD_S = 30.0


@dataclass(frozen=True)
class LivenessState:
    """Snapshot of liveness at a query instant.

    ``age_s`` is whole seconds since the last observed byte, truncated
    toward zero so a partial second never reads as "1s" on the bar.

    ``reason`` is the signal that decided the level: ``pty`` (recent
    bytes), ``cpu`` (recent CPU sample), ``silent`` (no PTY, no recent
    CPU but still within the working window), or ``stuck`` (both
    silent past their thresholds). Defaults to ``pty`` for backwards
    compatibility with callers that only care about ``level``.
    """

    level: LivenessLevel
    age_s: int
    reason: LivenessReason = "pty"


class HeartbeatTracker:
    def __init__(
        self,
        *,
        live_threshold_s: float = _DEFAULT_LIVE_THRESHOLD_S,
        stuck_threshold_s: float = _DEFAULT_STUCK_THRESHOLD_S,
    ) -> None:
        self._live_threshold_s = live_threshold_s
        self._stuck_threshold_s = stuck_threshold_s
        self._last_byte_at: float | None = None
        self._cpu_active_at: float | None = None

    def note_bytes(self, now: float) -> None:
        self._last_byte_at = now

    def note_cpu_sample(self, now: float, active: bool) -> None:
        if active:
            self._cpu_active_at = now

    def state(self, now: float) -> LivenessState | None:
        if self._last_byte_at is None:
            return None

        byte_age = now - self._last_byte_at
        cpu_age = (now - self._cpu_active_at) if self._cpu_active_at is not None else None
        age_s = int(byte_age)

        if byte_age < self._live_threshold_s:
            return LivenessState(level="live", age_s=age_s, reason="pty")

        # No recent bytes — but a fresh CPU sample means the subprocess
        # tree is doing real work right now. Keep the dot green.
        if cpu_age is not None and cpu_age < self._live_threshold_s:
            return LivenessState(level="live", age_s=age_s, reason="cpu")

        if byte_age < self._stuck_threshold_s:
            return LivenessState(level="working", age_s=age_s, reason="silent")

        # Past the stuck threshold on bytes alone — last hope is a
        # recent CPU sample within the same window.
        if cpu_age is not None and cpu_age < self._stuck_threshold_s:
            return LivenessState(level="working", age_s=age_s, reason="cpu")

        return LivenessState(level="stuck", age_s=age_s, reason="stuck")
