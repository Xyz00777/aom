"""R13 — cap ``PtyStreamParser._recap_lines`` at ``MAX_LOG_LINES``.

R13 spec: the ``POST_RUN_RECAP`` phase appends every plaintext line to
``_recap_lines`` for display at completion. A noisy ``PLAY RECAP`` block
(produced when ``-v`` is set, when a host hangs printing context, or
when a verbose module dumps intermediate output) can grow
``_recap_lines`` without bound. The plaintext_lines cap from R2 covers
``EXECUTION``-phase chatter; the recap tail is its own unbounded list.

Mirror the R2 pattern: cap at ``MAX_LOG_LINES`` and drop oldest first
when exceeded.
"""

from __future__ import annotations

from ansible_aom.core.parser import PtyStreamParser, StreamPhase
from ansible_aom.core.state_machine import MAX_LOG_LINES


def _recap_line(idx: int) -> str:
    return f"web1    : ok=42 changed=0 unreachable=0 failed=0 skipped=99 iter={idx}"


def test_recap_lines_capped_at_max_log_lines() -> None:
    """R13: recap_lines must not exceed MAX_LOG_LINES."""
    parser = PtyStreamParser()
    parser.phase = StreamPhase.POST_RUN_RECAP
    # Feed MAX_LOG_LINES + 100 recap lines.
    for i in range(MAX_LOG_LINES + 100):
        parser.feed_line(_recap_line(i))
    assert len(parser.recap_lines) == MAX_LOG_LINES


def test_recap_lines_keeps_most_recent_when_capped() -> None:
    """R13: the retained tail must be the most-recent lines.

    Same reasoning as R2's plaintext_lines test: a stuck head defeats
    the diagnostic purpose of recap_lines (the user wants to see what
    was in the recap at the moment of completion).
    """
    parser = PtyStreamParser()
    parser.phase = StreamPhase.POST_RUN_RECAP
    for i in range(MAX_LOG_LINES + 100):
        parser.feed_line(_recap_line(i))
    # Last retained entry should be the most recent.
    assert parser.recap_lines[-1] == _recap_line(MAX_LOG_LINES + 100 - 1)
    # First retained entry should be the oldest survivor (line at
    # index 100, since 100 lines were dropped).
    assert parser.recap_lines[0] == _recap_line(100)


def test_recap_lines_pin_against_constant_drift() -> None:
    """R13: pin the cap value at MAX_LOG_LINES (=50000)."""
    parser = PtyStreamParser()
    parser.phase = StreamPhase.POST_RUN_RECAP
    assert MAX_LOG_LINES == 50_000
    # Feed exactly 50_000 lines — no truncation should occur.
    for i in range(MAX_LOG_LINES):
        parser.feed_line(_recap_line(i))
    assert len(parser.recap_lines) == MAX_LOG_LINES
