"""ReplayDriver — :class:`EventSource` that re-emits a recorded session.

Thin facade over :func:`ansible_aom.replay.replay_session`. The
replay loop, timestamp scheduling, and session-loading logic stay in
``replay.py`` until §7.2 promotes this module to be their host;
this driver owns the parameter storage and the ``drive()`` boundary.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from ansible_aom.renderer.protocol import Renderer


class ReplayDriver:
    """Re-stream a previously recorded session through a :class:`Renderer`.

    Mirrors the keyword arguments accepted by
    :func:`ansible_aom.replay.replay_session`.
    """

    def __init__(
        self,
        session_dir: Path,
        session_id: str,
        *,
        speed: float = 1.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session_dir = session_dir
        self._session_id = session_id
        self._speed = speed
        self._sleeper = sleeper

    @property
    def session_id(self) -> str:
        return self._session_id

    def drive(self, renderer: Renderer) -> int:
        from ansible_aom.replay import replay_session

        return replay_session(
            session_dir=self._session_dir,
            session_id=self._session_id,
            renderer=renderer,
            speed=self._speed,
            sleeper=self._sleeper,
        )
