"""Replay a recorded AOM session through a Renderer (F2).

Reads ``events.jsonl`` + ``meta.json`` from
``<session_dir>/<session_id>/`` and feeds each event into the
provided renderer at the original ``_timestamp`` cadence (or scaled
by ``speed``). The renderer interface is identical to the one
``runner.run_playbook`` drives, so the replay command can use the
same factory-built CompactRenderer or AOMApp.

Replay deliberately reproduces ONLY what's in ``events.jsonl``. AOM-
emitted artefacts that never made it into the JSONL stream are not
replayed:

* ``renderer.add_warning(...)`` calls (preflight errors, R3
  recording-disabled warning, deprecation surfacing).
* The preflight summary (``set_definitions`` is NOT called — the
  renderer rebuilds its tree from ``v2_playbook_on_play_start`` /
  ``v2_playbook_on_task_start`` events).
* Password-prompt log lines emitted by the runner.
* stderr lines from ``stderr.log``.

Document this in ``aom replay --help`` (see ``cli._run_replay``).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from ansible_aom.core.session import load_session
from ansible_aom.renderer.protocol import Renderer


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO 8601 ``_timestamp`` field; return None when unparseable."""
    if not isinstance(value, str) or not value:
        return None
    try:
        # Replace trailing Z with +00:00 because fromisoformat (pre-3.11
        # was strict; 3.11+ accepts Z but be explicit anyway).
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def replay_session(
    session_dir: Path,
    session_id: str,
    renderer: Renderer,
    speed: float = 1.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> int:
    """Replay ``session_id`` from ``session_dir`` through ``renderer``.

    Args:
        session_dir: Directory containing per-session subdirectories
            (typically ``~/.local/state/aom/sessions``).
        session_id: The UUIDv7 (or partial / arbitrary name) directory
            under ``session_dir`` to replay.
        renderer: Any object satisfying the ``Renderer`` protocol.
        speed: Playback rate. ``1.0`` = real time. ``2.0`` = twice as
            fast. ``0`` (or any falsy value) = no sleeps; events fire
            back-to-back.
        sleeper: Injectable sleep function for tests. Defaults to
            ``time.sleep``.

    Returns:
        ``0`` on a successful replay, ``1`` when the session can't be
        loaded.
    """
    session = load_session(session_id, session_dir)
    if session is None:
        return 1

    playbook = session.get("playbook", "")
    events = list(session.get("events", []))

    renderer.start(playbook, [])
    try:
        for event in events:
            renderer.update_state(event)
    finally:
        # Final completion derived from meta.json status; default to
        # "completed" when missing. Tasks 9 + 10 will widen this.
        status = str(session.get("status") or "completed")
        renderer.handle_completion(0, status)
        renderer.stop()
    return 0
