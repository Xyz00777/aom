"""R11 — tighter post-stats EOF watchdog once ``end_time`` is set.

R11 spec: the 30 s ``_EOF_WATCHDOG_S`` is appropriate as a *first*
post-stats window — a child that was just about to close its PTY might
take a while to actually do so once the orchestrator's stats are
written. Once ``v2_playbook_on_stats`` has been *fully consumed* and
the run's ``end_time`` is recorded, however, anything more than a few
seconds of post-stats silence is almost certainly a hung PTY (forked
child holding the fd open). Switch to a 5 s quiet watchdog then.

The check is observable from inside ``_drive`` via the
``state.end_time`` attribute the runner populates. Tests exercise it
by:

1. Driving the parser past ``v2_playbook_on_stats`` (flips phase to
   ``POST_RUN_RECAP`` and — through the state plumbing — sets
   ``state.end_time``).
2. Asserting the *next* ``child.expect`` call is invoked with a timeout
   at or below the quiet bound (5 s), not the full 30 s.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

from ansible_aom.ansible.runner import (
    _EOF_WATCHDOG_S,
    _EOF_WATCHDOG_S_QUIET,
    _drive,
)
from ansible_aom.core.parser import PtyStreamParser, StreamPhase
from ansible_aom.core.run_state import RunState


def _start_line() -> str:
    return json.dumps({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"})


def _stats_line() -> str:
    return json.dumps({"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"})


class _RecordingChild:
    """Fake pexpect child that records every expect() timeout and never hangs.

    After the canned newline responses are exhausted, every further
    ``expect()`` call returns TIMEOUT (idx 2) so ``_drive`` keeps
    looping without blocking. We record the *timeout kwarg* of every
    call so the test can verify the watchdog dropped from
    ``_EOF_WATCHDOG_S`` (30 s) to ``_EOF_WATCHDOG_S_QUIET`` (5 s) once
    ``state.end_time`` is set.
    """

    def __init__(self, responses: list[tuple[int, str, str]]) -> None:
        self._responses = list(responses)
        self.timeouts_seen: list[float] = []
        self.before: str = ""
        self.after: str = ""
        self.exitstatus: int | None = 0
        self.signalstatus: int | None = None
        self.buffer: str = ""
        self.pid = 0
        self.closed = False
        # Stay "alive" so R10's isalive check doesn't bail out before
        # we observe the watchdog transition.
        self.alive = True

    def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
        self.timeouts_seen.append(timeout)
        if self._responses:
            idx, before, after = self._responses.pop(0)
            self.before = before
            self.after = after
            return idx
        # Always return TIMEOUT (idx 2) — pre-stats before stats is
        # delivered we never enter this branch; after stats the
        # post-stats watchdog path uses the timeout we just recorded.
        return 2

    def isalive(self) -> bool:
        return self.alive

    def close(self, force: bool = False) -> None:  # noqa: ARG002
        self.closed = True


def _drive_short(child: Any, parser: PtyStreamParser, state: RunState) -> None:
    """Run ``_drive`` with a renderer+sink that prevent pexpect errors.

    The dummy renderer returns ``""`` for any prompt handler, so a
    password match (if it accidentally fires) doesn't block. We bound
    the call by raising from ``close()`` after a short number of
    expect() calls — the test only inspects ``timeouts_seen`` after
    ``_drive`` returns, not the return value.
    """
    renderer = MagicMock()
    renderer.handle_password_prompt.return_value = ""
    sink = MagicMock()
    _drive(child, parser, state, renderer, timeout=0.05, sink=sink)


def test_post_stats_watchdog_drops_to_quiet_after_end_time() -> None:
    """R11: after ``state.end_time`` is set, post-stats timeout shrinks.

    The runner consumes ``v2_playbook_on_stats`` and (with R11 wiring)
    also feeds the event through ``RunState.handle_event`` so
    ``state.end_time`` is populated. Subsequent ``expect`` calls in
    POST_RUN_RECAP must use ``_EOF_WATCHDOG_S_QUIET`` (5 s), not the
    full ``_EOF_WATCHDOG_S`` (30 s).
    """
    parser = PtyStreamParser()
    state = RunState(playbook="x")

    # Feed a stats line through state to flip end_time. We do this
    # directly because the integration is verified by other tests; here
    # we just need the side-effect (end_time set) to observe the
    # watchdog transition.
    state.handle_event(json.loads(_stats_line()))
    assert state.end_time is not None, "test prerequisite: stats event must populate end_time"

    child = _RecordingChild(
        [
            (0, "", _start_line() + "\n"),  # newline match for start
            (0, "", _stats_line() + "\n"),  # newline match for stats
        ]
    )
    # Pre-populate parser phase by feeding start + stats through it too,
    # so _drive sees POST_RUN_RECAP on the very first iteration.
    parser.feed_line(_start_line())
    parser.feed_line(_stats_line())
    assert parser.phase == StreamPhase.POST_RUN_RECAP

    _drive_short(child, parser, state)

    # Last expect() call should have used the quiet watchdog, not the
    # full 30 s.
    assert child.timeouts_seen, "expected at least one expect() call"
    assert child.timeouts_seen[-1] == _EOF_WATCHDOG_S_QUIET, (
        f"post-stats watchdog expected to drop to "
        f"{_EOF_WATCHDOG_S_QUIET} once end_time is set, got "
        f"{child.timeouts_seen[-1]} (all calls: {child.timeouts_seen!r})"
    )


def test_pre_end_time_uses_full_watchdog() -> None:
    """R11: until stats is consumed, full ``_EOF_WATCHDOG_S`` applies.

    Once the parser flips to POST_RUN_RECAP but ``state.end_time`` is
    still ``None`` (e.g. a run where the runner recorded the phase flip
    before feeding the event through state — defensive), the watchdog
    stays at the full 30 s. Catches a regression where the quiet
    watchdog fires too eagerly.
    """
    parser = PtyStreamParser()
    state = RunState(playbook="x")
    # Deliberately do NOT feed stats through state — end_time stays None.
    parser.feed_line(_start_line())
    parser.feed_line(_stats_line())
    assert parser.phase == StreamPhase.POST_RUN_RECAP
    assert state.end_time is None

    child = _RecordingChild(
        [
            (0, "", _start_line() + "\n"),
            (0, "", _stats_line() + "\n"),
        ]
    )
    _drive_short(child, parser, state)

    assert child.timeouts_seen[-1] == _EOF_WATCHDOG_S, (
        f"pre-end_time post-stats watchdog must stay at full "
        f"{_EOF_WATCHDOG_S}, got {child.timeouts_seen[-1]}"
    )


def test_quiet_constant_is_smaller_than_full_watchdog() -> None:
    """R11 invariant: ``_EOF_WATCHDOG_S_QUIET`` < ``_EOF_WATCHDOG_S``.

    The whole point of R11 is that the quiet watchdog is *shorter* than
    the full one — otherwise there is no behaviour change to test.
    Pin the ordering against accidental constant swap.
    """
    assert _EOF_WATCHDOG_S_QUIET < _EOF_WATCHDOG_S, (
        f"_EOF_WATCHDOG_S_QUIET ({_EOF_WATCHDOG_S_QUIET}) must be smaller "
        f"than _EOF_WATCHDOG_S ({_EOF_WATCHDOG_S})"
    )
    assert _EOF_WATCHDOG_S_QUIET >= 1.0, (
        f"_EOF_WATCHDOG_S_QUIET must be at least 1s for legitimate "
        f"post-stats cleanup, got {_EOF_WATCHDOG_S_QUIET}"
    )
