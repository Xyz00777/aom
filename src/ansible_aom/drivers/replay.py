"""Replay a recorded AOM session through a Renderer (F2).

Both halves of the replay subcommand live here:

* :func:`replay_session` reads ``events.jsonl`` + ``meta.json`` from
  ``<session_dir>/<session_id>/`` and feeds each event into the
  provided renderer at the original ``_timestamp`` cadence (or scaled
  by ``speed``). The renderer interface is identical to the one the
  live runner drives, so the replay command can use the same
  factory-built CompactRenderer or AOMApp.
* :class:`ReplayDriver` wraps that loop behind the :class:`EventSource`
  protocol so ``cli.py`` only sees the two-protocol composition root.

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

Document this in ``aom replay --help`` (see :func:`cli_main`).
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import argcomplete

from ansible_aom.session.store import load_session
from ansible_aom.renderer.factory import create_renderer
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
        ``0`` on a successful replay, ``130`` if the user pressed
        Ctrl+C mid-replay (mirrors :func:`runner.run_playbook`), ``1``
        when the session can't be loaded.
    """
    session = load_session(session_id, session_dir)
    if session is None:
        return 1

    playbook = session.get("playbook", "")
    events = list(session.get("events", []))

    renderer.start(playbook, [])
    interrupted = False
    try:
        previous_ts: datetime | None = None
        for event in events:
            current_ts = _parse_timestamp(event.get("_timestamp"))
            if previous_ts is not None and current_ts is not None and speed:
                # Negative deltas can occur when ansible callbacks fire
                # from different threads. Clamp to zero so we never call
                # sleep with a negative argument.
                delta = (current_ts - previous_ts).total_seconds()
                if delta < 0:
                    delta = 0.0
                wait = delta / float(speed)
                if wait > 0:
                    sleeper(wait)
            renderer.update_state(event)
            if current_ts is not None:
                previous_ts = current_ts
    except KeyboardInterrupt:
        interrupted = True
    finally:
        if interrupted:
            renderer.handle_completion(130, "crashed")
        else:
            status = str(session.get("status") or "completed")
            renderer.handle_completion(0, status)
        renderer.stop()
    return 130 if interrupted else 0


class ReplayDriver:
    """Re-stream a previously recorded session through a :class:`Renderer`.

    Mirrors the keyword arguments accepted by :func:`replay_session`.
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
        return replay_session(
            session_dir=self._session_dir,
            session_id=self._session_id,
            renderer=renderer,
            speed=self._speed,
            sleeper=self._sleeper,
        )


_REPLAY_HELP_EPILOG = """\
Replay reads <session-id>/events.jsonl and <session-id>/meta.json from
the AOM state directory (default ~/.local/state/aom/sessions) and
feeds the recorded events through the renderer of your choice.

Speed control:
  --speed 1    real time (default)
  --speed 10   ten times faster
  --speed 0    as fast as possible (no sleeps)

  Note: a real 8-hour run replayed at 1x sleeps for 8 hours.
  Use --speed 10 (or higher) — or --speed 0 — for long sessions.

What replay does NOT reproduce:
  * AOM-emitted warnings (preflight, deprecations, R3 disk-disabled).
  * The preflight summary — definitions are rebuilt from
    v2_playbook_on_play_start / v2_playbook_on_task_start events.
  * Password-prompt log lines.
  * stderr lines from stderr.log.

Anything else that appeared in events.jsonl is replayed verbatim.
"""


def _build_parser() -> argparse.ArgumentParser:
    """Build the ``aom replay`` argument parser.

    Factored out of :func:`cli_main` so shell-completion glue can
    introspect the parser shape without invoking dispatch.
    """
    from ansible_aom.completion import session_id_completer

    parser = argparse.ArgumentParser(
        prog="aom replay",
        description="Replay a recorded AOM session through the renderer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_REPLAY_HELP_EPILOG,
    )
    session_action = parser.add_argument(
        "session_id", help="Session ID (UUIDv7 directory name) to replay"
    )
    session_action.completer = session_id_completer
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".local" / "state" / "aom" / "sessions",
        help="Directory containing session subdirectories (default: %(default)s)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help=(
            "Playback rate. 1.0 = real time, 10 = 10x faster, 0 = no sleeps. "
            "Use a high speed for long sessions."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--compact",
        dest="mode",
        action="store_const",
        const="compact",
        help="Use the compact renderer (default)",
    )
    mode.add_argument(
        "--tui",
        dest="mode",
        action="store_const",
        const="tui",
        help="Use the full multi-panel Textual TUI",
    )
    parser.set_defaults(mode="compact")

    argcomplete.autocomplete(parser)
    return parser


def cli_main(argv: list[str]) -> int:
    """Entry point for ``aom replay <session-id> [...]``.

    Argparse the supplied tail (``sys.argv[2:]`` from the top-level
    dispatcher), build a renderer via the shared factory, and call
    ``ReplayDriver.drive``. The exit code mirrors :func:`replay_session`:

    * ``0`` — replay finished
    * ``1`` — session not found
    * ``130`` — Ctrl+C mid-replay
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    renderer = create_renderer(mode=args.mode, is_tty=sys.stdout.isatty())
    driver = ReplayDriver(
        session_dir=args.state_dir,
        session_id=args.session_id,
        speed=float(args.speed),
    )
    return driver.drive(renderer)
