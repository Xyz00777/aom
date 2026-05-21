"""Pure formatters for durations and relative ages.

These functions are used wherever AOM needs to surface a wall-clock
interval to the user in a tight horizontal budget — the compact
renderer's "Last run" hint today, and any future ETA / status-bar
elapsed display tomorrow.

Lives in ``core/`` so multiple infrastructure callers
(``compact/format.py``, ``tui/``, …) can share one definition without
crossing the layering rule that forbids infra-to-infra imports.

Pure: no I/O, no logging, no global state. ``format_age`` uses
``datetime.now(timezone.utc)`` — the only impure-looking call here —
but that's a deterministic projection of the system clock at call
time, not state owned by the module.
"""

from __future__ import annotations

from datetime import datetime, timezone


def format_duration_compact(seconds: float) -> str:
    """Render a duration as the most compact human form ("42s", "1m23s", "1h05m").

    Resolution is one second: sub-second values round to the nearest
    second. The buckets are chosen so the result is always at most
    six characters wide (``"99h59m"``) — small enough to fit beside
    other status segments without overflowing on narrow terminals.
    """
    if seconds < 60:
        return f"{int(round(seconds))}s"
    if seconds < 3600:
        m, s = divmod(int(round(seconds)), 60)
        return f"{m}m{s:02d}s"
    h, rem = divmod(int(round(seconds)), 3600)
    m = rem // 60
    return f"{h}h{m:02d}m"


def format_age(end_time: datetime) -> str:
    """Render an absolute UTC ``end_time`` as a relative ``"Xs/m/h/d ago"`` string.

    The granularity drops one tier per order of magnitude — minutes
    once the gap exceeds 60 s, hours once it exceeds an hour, days
    once it exceeds a day. The "ago" suffix is included so callers can
    drop the string into a sentence without further glue.
    """
    delta = datetime.now(timezone.utc) - end_time
    # Clamp negative deltas to 0 — clock skew (NFS sessions across
    # machines, manual clock reset, hand-edited meta.json) shouldn't
    # surface as ``-3s ago`` in the UI.
    secs = max(int(delta.total_seconds()), 0)
    if secs < 60:
        return f"{secs}s ago"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"
