"""Batch E item #10c — R8 no-EOF hang protection.

A misbehaved (or hung) ansible-playbook child can emit a complete event
stream — including the final ``v2_playbook_on_stats`` — and then never
close stdout, never exit. The runner's ``_drive`` loop is happy to keep
waiting on ``child.expect(...)`` for as long as the timeout allows.

**Current behavior**: there is no bounded-wait after ``playbook_on_stats``.
The runner waits for EOF or for the (long) idle timeout to trigger.

This test pins that behavior as an **xfail** so the gap is visible in
the suite but doesn't block CI. When/if a 2-second post-stats grace
window is implemented in ``_drive``, flip the xfail off and the test
becomes a regression marker.

The shim writes complete events then enters a long sleep without closing
stdout. We invoke the runner with a tight wall-clock budget and assert
that ``run_playbook`` returns within that budget regardless.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from unittest.mock import MagicMock, patch

import pytest


def _fake_ansible_hangs_after_stats(
    events: list[dict], sleep_seconds: int = 60
) -> tuple[str, list[str]]:
    """Build a fake-ansible command that emits events then sleeps without
    closing stdout. Mimics a child that processed everything but failed
    to ``sys.exit``.
    """
    payload = json.dumps(events)
    code = (
        "import json, sys, time; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        f"time.sleep({sleep_seconds})"
    )
    return sys.executable, ["-c", code]


@pytest.mark.xfail(
    strict=False,
    reason=(
        "R8 spec gap: runner has no post-playbook_on_stats grace timeout; "
        "child that emits all events and then refuses to close stdout will "
        "block the expect-loop until the (long) per-read timeout. Test "
        "captures the desired behavior; flip strict=True once the bounded "
        "wait is implemented in runner._drive."
    ),
)
def test_runner_returns_within_bounded_time_when_child_hangs_after_stats() -> None:
    """The runner should not wait indefinitely on a hung child once the
    final stats event has been consumed."""
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    cmd, args = _fake_ansible_hangs_after_stats(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ],
        sleep_seconds=30,
    )

    # Run the runner on a worker thread; if it doesn't return within 5s,
    # we know the EOF wait is unbounded and this test xfails as designed.
    result: dict[str, int | None] = {"exit_code": None}

    def _drive_runner() -> None:
        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            # Short per-read timeout so the worker thread can react,
            # but the run as a whole should still complete bounded.
            result["exit_code"] = run_playbook("playbook.yml", [], renderer, timeout=0.5)

    worker = threading.Thread(target=_drive_runner, daemon=True)
    worker.start()
    worker.join(timeout=5.0)

    assert not worker.is_alive(), (
        "run_playbook did not return within 5s after the child stopped "
        "emitting events — bounded post-stats wait not implemented (R8)"
    )
    assert result["exit_code"] is not None


def test_runner_finishes_promptly_on_clean_eof() -> None:
    """Sanity baseline: when the child cleanly exits after emitting all
    events, the runner returns quickly. Pairs with the xfail above so the
    contrast (clean EOF vs hung EOF) is documented in one place."""
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    payload = json.dumps(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ]
    )
    code = (
        "import json, sys; "
        f"events = json.loads({payload!r}); "
        "[sys.stdout.write(json.dumps(e) + '\\n') for e in events]; "
        "sys.stdout.flush(); "
        "sys.exit(0)"
    )

    start = time.monotonic()
    with patch("ansible_aom.ansible.runner._build_command", return_value=(sys.executable, ["-c", code])):
        exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)
    elapsed = time.monotonic() - start

    assert exit_code == 0
    assert elapsed < 5.0, f"clean EOF should be sub-5s, took {elapsed:.2f}s"
