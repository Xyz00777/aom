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

    no bytes ever                 → None
    age < live_threshold_s        → LIVE
    age < stuck_threshold_s       → WORKING
    cpu active within stuck win.  → WORKING
    otherwise                     → STUCK

The runner is expected to call ``reset()`` on each new task so a
stuck-from-previous-task glyph does not bleed into the next task's
first second.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LivenessLevel = Literal["live", "working", "stuck"]

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
    """

    level: LivenessLevel
    age_s: int


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

    def reset(self) -> None:
        self._last_byte_at = None
        self._cpu_active_at = None

    def state(self, now: float) -> LivenessState | None:
        if self._last_byte_at is None:
            return None

        age = now - self._last_byte_at
        age_s = int(age)

        if age < self._live_threshold_s:
            return LivenessState(level="live", age_s=age_s)

        if age < self._stuck_threshold_s:
            return LivenessState(level="working", age_s=age_s)

        # Past the stuck threshold on bytes alone — last hope is a
        # recent CPU sample within the same window.
        if (
            self._cpu_active_at is not None
            and (now - self._cpu_active_at) < self._stuck_threshold_s
        ):
            return LivenessState(level="working", age_s=age_s)

        return LivenessState(level="stuck", age_s=age_s)
