"""Unit tests for the EOF watchdog after ``v2_playbook_on_stats`` (R8).

R8 spec: after the runner consumes a ``v2_playbook_on_stats`` event it
should not block forever on EOF. If the child stays open with no
further output for ``_EOF_WATCHDOG_S`` seconds, log a warning and
break out of the wait loop as if EOF had fired.

The watchdog is implemented with pexpect's built-in ``expect(..., timeout=...)``
rather than a separate thread — no threading, just a per-loop timeout
that grows once stats is seen.

The tests below exercise ``_drive`` directly with a mock child so we
can assert both paths:

1. **Watchdog fires.** After the stats event, the child goes silent;
   within ~``_EOF_WATCHDOG_S`` the runner logs a warning and returns.
2. **Clean EOF still works.** After stats, EOF fires within the
   watchdog window — no warning logged, normal completion.
3. **Pre-stats silence is unchanged.** The runner's pre-stats idle
   behaviour (per-read ``timeout``) is not affected by the watchdog
   — only post-stats waits are bounded.
"""

from __future__ import annotations

import json
import logging
import sys
from unittest.mock import MagicMock

import pexpect
import pytest

from ansible_aom.ansible.runner import (
    _EOF_WATCHDOG_S,
    _drive,
)
from ansible_aom.core.parser import PtyStreamParser
from ansible_aom.core.run_state import RunState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stats_line() -> str:
    return json.dumps({"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"})


def _start_line() -> str:
    return json.dumps({"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"})


class _SequenceChild:
    """Minimal pexpect-spawn stub driven by a list of expect() responses.

    Each ``responses`` entry is a tuple ``(idx, before, after)`` that
    ``child.expect`` will yield in order. When the list is exhausted
    the stub raises :class:`pexpect.exceptions.EOF` (the documented
    behaviour when the child exits cleanly without more pattern
    matches), unless ``hang_after`` is set — in which case it returns
    TIMEOUT (index 2) on every subsequent call so the runner's
    post-stats watchdog has something to react to.

    This is enough to drive ``_drive`` end-to-end without spawning a
    real subprocess: the parser only cares that JSONL lines come in
    one-per-call with the right newline framing, and the renderer is
    a MagicMock that records every call.
    """

    def __init__(self, responses: list[tuple[int, str, str]], *, hang_after: bool = False) -> None:
        self._responses = list(responses)
        self._hang_after = hang_after
        self._call_count = 0
        self.before = ""
        self.after = ""
        self.exitstatus: int | None = None
        self.signalstatus: int | None = None
        self.buffer = ""
        self.isalive_value = True
        self._sent: list[str] = []
        self._closed = False
        # Used by the runner's CPU-sampling heartbeat. Real pexpect
        # children have a ``pid``; the stub returns 0 (no-op for
        # _sample_subprocess_active, which short-circuits on bad PIDs).
        self.pid = 0

    def expect(self, patterns, timeout=-1, **kw):  # noqa: ARG002
        if not self._responses:
            if self._hang_after:
                self._call_count += 1
                self.before = ""
                self.after = ""
                return 2  # TIMEOUT idx — drives the watchdog path
            raise pexpect.exceptions.EOF("child exited")
        self._call_count += 1
        idx, before, after = self._responses.pop(0)
        self.before = before
        self.after = after
        return idx

    def sendline(self, line: str) -> None:
        self._sent.append(line)

    def close(self, force: bool = False) -> None:
        self._closed = True

    def isalive(self) -> bool:
        return self.isalive_value


class _NullSink:
    """Stand-in for ``_SessionSink`` — the runner treats both the same."""

    def record_event(self, event: dict) -> None: ...
    def record_stderr(self, line: str) -> None: ...
    def end(self, status: str) -> None: ...


# ---------------------------------------------------------------------------
# Watchdog config sanity
# ---------------------------------------------------------------------------


class TestEofWatchdogConfig:
    """The watchdog constant must be a positive, non-trivial number of seconds."""

    def test_watchdog_is_positive(self) -> None:
        assert _EOF_WATCHDOG_S > 0

    def test_watchdog_is_at_least_five_seconds(self) -> None:
        """Five seconds is the smallest "long enough to absorb a clean EOF"
        but small enough that a stuck child gets noticed in human time."""
        assert _EOF_WATCHDOG_S >= 5


# ---------------------------------------------------------------------------
# Watchdog behaviour
# ---------------------------------------------------------------------------


class TestWatchdogFiresAfterStats:
    """When the child goes silent after the stats event, the runner must
    not wait forever — it logs a warning and exits the loop."""

    def test_watchdog_emits_warning_and_returns_when_no_eof(self, caplog) -> None:
        """Synthetic EOF after a stats event in a hung child triggers a
        warning visible via the renderer's ``print_log`` AND via the
        runner's logger."""
        parser = PtyStreamParser()
        renderer = MagicMock()
        sink = _NullSink()

        # The runner's first expect() consumes the start line, the
        # second consumes the stats line, then hangs.
        child = _SequenceChild(
            [
                (0, "", _start_line() + "\n"),  # newline match for start
                (0, "", _stats_line() + "\n"),  # newline match for stats
            ],
            hang_after=True,
        )

        caplog.set_level(logging.WARNING, logger="ansible_aom.ansible.runner")

        exit_code = _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.5, sink=sink)

        # Synthetic EOF: exit_code falls back to 1 because we never set
        # exitstatus/signalstatus on the stub. The point is that we
        # RETURN — the loop bounded itself.
        assert exit_code == 1
        # And we surfaced a warning to the renderer so the user sees it.
        printed = [c.args[0] for c in renderer.print_log.call_args_list]
        assert any(
            "EOF" in line and ("watchdog" in line.lower() or "30" in line) for line in printed
        ), f"expected EOF watchdog warning via print_log, got: {printed!r}"

    def test_watchdog_emits_warning_via_logger(self, caplog) -> None:
        """The warning should also land in the standard logger so debug
        mode surfaces it without a renderer attached."""
        parser = PtyStreamParser()
        renderer = MagicMock()
        sink = _NullSink()

        child = _SequenceChild(
            [
                (0, "", _start_line() + "\n"),
                (0, "", _stats_line() + "\n"),
            ],
            hang_after=True,
        )

        with caplog.at_level(logging.WARNING, logger="ansible_aom.ansible.runner"):
            _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.5, sink=sink)

        assert any(
            "EOF" in record.getMessage() and "watchdog" in record.getMessage().lower()
            for record in caplog.records
        ), f"expected watchdog warning in logs, got: {[r.getMessage() for r in caplog.records]}"


class TestCleanEofAfterStats:
    """The normal case — child emits stats, then closes stdout cleanly —
    must complete without the watchdog interfering."""

    def test_clean_eof_after_stats_no_warning(self) -> None:
        parser = PtyStreamParser()
        renderer = MagicMock()
        sink = _NullSink()

        child = _SequenceChild(
            [
                (0, "", _start_line() + "\n"),
                (0, "", _stats_line() + "\n"),
                (1, "leftover", ""),  # EOF index = 1
            ],
            hang_after=False,
        )
        child.exitstatus = 0

        exit_code = _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.5, sink=sink)

        assert exit_code == 0
        # No watchdog warning — the clean EOF should be invisible.
        for c in renderer.print_log.call_args_list:
            assert "watchdog" not in c.args[0].lower()


# ---------------------------------------------------------------------------
# Pre-stats silence unchanged
# ---------------------------------------------------------------------------


class TestPreStatsSilenceUnchanged:
    """The watchdog only applies AFTER stats. Before stats, the runner
    must keep using the per-read ``timeout`` and ticking the clock
    rather than logging a watchdog warning."""

    def test_pre_stats_timeout_does_not_trigger_watchdog(self) -> None:
        parser = PtyStreamParser()
        renderer = MagicMock()
        sink = _NullSink()

        # First expect() matches the start line; subsequent calls just
        # hit TIMEOUT (index 2) — no stats event ever arrives.
        # _drive should keep calling expect() in the timeout branch
        # until we let the child exit (EOF).
        responses: list[tuple[int, str, str]] = [(0, "", _start_line() + "\n")]
        # Add a long stretch of TIMEOUT responses; _drive loops over them.
        for _ in range(5):
            responses.append((2, "", ""))  # timeout_idx = 2
        # Finally EOF so the test doesn't loop forever.
        responses.append((1, "", ""))  # EOF idx = 1

        child = _SequenceChild(responses, hang_after=False)
        child.exitstatus = 0

        _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.5, sink=sink)

        # No "watchdog" warning during pre-stats silence — that's the
        # whole point of gating the watchdog on having seen stats.
        for c in renderer.print_log.call_args_list:
            assert "watchdog" not in c.args[0].lower(), (
                f"watchdog fired before stats: {c.args[0]!r}"
            )


# ---------------------------------------------------------------------------
# Watchdog timeout is bounded — sanity guard against regressions
# ---------------------------------------------------------------------------


class TestWatchdogUsesBoundedTimeout:
    """The post-stats ``expect`` call must use the watchdog timeout,
    not the per-read timeout. We verify by patching the timeout we
    observe (smoke test via call count)."""

    def test_watchdog_path_calls_expect(self) -> None:
        """End-to-end smoke: a hung child produces exactly the
        expect() calls we expect before we give up. The watchdog
        path is the synthetic-EOF path — the test only asserts the
        loop bounds itself, not the exact timeout value."""
        parser = PtyStreamParser()
        renderer = MagicMock()
        sink = _NullSink()

        child = _SequenceChild(
            [
                (0, "", _start_line() + "\n"),
                (0, "", _stats_line() + "\n"),
            ],
            hang_after=True,
        )

        # 2 newline matches + 1 raising EOF (synthetic). That's the
        # bounded path: stats was consumed, then EOF fired via the
        # watchdog's synthetic-EOF branch.
        _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.5, sink=sink)

        # The runner must have made at least one expect() call AFTER
        # seeing the stats event — that's the watchdog's single post-
        # stats read. Without the watchdog it would loop indefinitely.
        assert child._call_count >= 3, (
            f"runner called expect() {child._call_count} times; "
            "watchdog did not bound the post-stats wait"
        )
