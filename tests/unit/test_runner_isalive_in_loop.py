"""R10 — `child.isalive()` check inside `_drive()` loop.

R10 spec: pexpect's EOF detection misses the "child exited but PTY fd
inherited by grandchild" case. The orchestrator process can spawn a
forked subprocess (common with ``become_user`` nested ``sudo``) and the
outer process exits cleanly, freeing the ansible-playbook process
itself — but the inherited PTY fd keeps the stream open and pexpect's
``expect(..., timeout=N)`` happily returns newline matches forever.

Without a liveness check, the loop would otherwise burn the full 30 s
post-stats watchdog before R8's synthetic-EOF fires. With ``isalive()``
checked after each ``expect()`` call we exit within a single ``timeout``
window of detecting the death.

The test below constructs a fake child that returns newline matches
forever (``isalive()`` False) and asserts the loop terminates promptly
(``<2 s`` for our short ``expect`` timeout), not after the full 30 s
post-stats watchdog.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

from ansible_aom.ansible.runner import _drive
from ansible_aom.core.parser import PtyStreamParser, StreamPhase
from ansible_aom.core.run_state import RunState


class _FakeChildIsaliveDead:
    """Fake pexpect child whose PID is dead but PTY still buffers data.

    R10 scenario: ``expect()`` keeps matching newlines forever because
    the inherited PTY is still feeding bytes back from some inherited
    fd. ``isalive()`` returns False because the orchestrator process
    that spawned ansible-playbook has already exited.
    """

    def __init__(self, line_count: int) -> None:
        self._expect_calls = 0
        self._max_calls = line_count
        self.exitstatus: int | None = 0
        self.signalstatus: int | None = None
        self.before: str = ""
        self.after: str = "\n"
        self.buffer: str = ""
        self.pid = 1
        self.closed = False

    def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
        self._expect_calls += 1
        if self._expect_calls > self._max_calls:
            # Stop returning newlines so the test can't loop forever.
            raise RuntimeError("FakeChildIsaliveDead exhausted")
        # Pattern index 0 = newline (matches what _drive's patterns list
        # defines as newline_idx). ``after`` is what pexpect assigns the
        # matched text to.
        self.before = ""
        self.after = "\n"
        return 0

    def isalive(self) -> bool:
        # The whole point: the child has exited but the loop hasn't
        # noticed yet. Without R10's isalive check, _drive would just
        # keep consuming "newlines" forever (or until R8's 30s
        # watchdog).
        return False

    def close(self, force: bool = False) -> None:  # noqa: ARG002
        self.closed = True


def _build_parser_in_post_run_recap() -> PtyStreamParser:
    parser = PtyStreamParser()
    # Move into POST_RUN_RECAP so R8's 30s post-stats watchdog path is
    # active. With the R10 isalive check the loop should break *much*
    # sooner; without it the test would hang for 30s (and we'd kill it).
    parser.phase = StreamPhase.POST_RUN_RECAP
    return parser


def test_drive_exits_promptly_when_child_dead_but_pty_open() -> None:
    """R10: isalive() == False in POST_RUN_RECAP must terminate the loop.

    Without the isalive check, the post-stats 30s watchdog is the only
    safety net. With it, the loop exits on the first iteration after
    the child's death. We assert the wall time stays well under the
    30s watchdog (use 2s to leave generous slack for CI noise).
    """
    parser = _build_parser_in_post_run_recap()
    renderer = MagicMock()
    sink = MagicMock()
    # Short timeout so the test runs fast if isalive is *not* honored —
    # we'd still see ~30s. But we cap line_count to bound the loop's
    # worst case; if isalive is honored we'll break after 1 call.
    child = _FakeChildIsaliveDead(line_count=100_000)
    start = time.monotonic()
    exit_code = _drive(
        child,
        parser,
        RunState(playbook="x"),
        renderer,
        timeout=0.01,
        sink=sink,
        diag=None,  # noqa: F841
    )
    elapsed = time.monotonic() - start

    assert child.closed, "loop should close the child before returning"
    assert child._expect_calls <= 5, (
        f"loop should exit after very few expect() calls when child is dead, "
        f"but it made {child._expect_calls} calls in {elapsed:.2f}s"
    )
    assert elapsed < 2.0, (
        f"loop took {elapsed:.2f}s to exit when child was already dead — "
        f"R10 isalive check missing or ineffective"
    )
    assert exit_code == 0


def test_drive_isalive_check_handles_eof_exception_path() -> None:
    """R10: isalive() check must also run after a pexpect.exceptions.EOF.

    The EOF exception is the *normal* exit path — pexpect raises it
    when the child closes its PTY. After flushing the pending buffer
    we already break; the isalive() check is a defence in depth that
    still has to be cheap (don't add a redundant call). This test
    covers the success case so a future "skip isalive on EOF" mistake
    doesn't break the common path.
    """

    class _FakeChildEofIsaliveTrue:
        def __init__(self) -> None:
            self.exitstatus: int | None = 0
            self.signalstatus: int | None = None
            self.before: str = "leftover line"
            self.after: str = ""
            self.buffer: str = ""
            self.pid = 1
            self.closed = False

        def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002
            import pexpect

            raise pexpect.exceptions.EOF("eof")

        def isalive(self) -> bool:
            return True  # alive, EOF is the legitimate exit signal

        def close(self, force: bool = False) -> None:  # noqa: ARG002
            self.closed = True

    parser = _build_parser_in_post_run_recap()
    renderer = MagicMock()
    sink = MagicMock()
    child = _FakeChildEofIsaliveTrue()
    exit_code = _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.01, sink=sink)
    assert child.closed
    assert exit_code == 0


def test_drive_isalive_check_on_timeout_branch() -> None:
    """R10: isalive() False on a TIMEOUT match must break the loop.

    The TIMEOUT branch is the slow path; if the child dies during a
    long timeout window we still want to exit on the same iteration
    rather than waiting for the next watchdog tick. Verifies the check
    covers all three post-expect code paths (newline, eof, timeout).
    """

    class _FakeChildTimeoutIsaliveDead:
        def __init__(self) -> None:
            self._calls = 0
            self.exitstatus: int | None = 0
            self.signalstatus: int | None = None
            self.before: str = ""
            self.after: str = ""
            self.buffer: str = ""
            self.pid = 1
            self.closed = False

        def expect(self, patterns: Any, timeout: float = 0) -> int:  # noqa: ARG002

            self._calls += 1
            # pattern index 2 = TIMEOUT
            return 2

        def isalive(self) -> bool:
            return False

        def close(self, force: bool = False) -> None:  # noqa: ARG002
            self.closed = True

    parser = _build_parser_in_post_run_recap()
    renderer = MagicMock()
    sink = MagicMock()
    child = _FakeChildTimeoutIsaliveDead()
    start = time.monotonic()
    _drive(child, parser, RunState(playbook="x"), renderer, timeout=0.05, sink=sink)
    elapsed = time.monotonic() - start
    assert child.closed
    assert child._calls <= 5, f"expected <=5 expect() calls, got {child._calls}"
    assert elapsed < 2.0, f"loop took {elapsed:.2f}s — should exit on first isalive()=False"
