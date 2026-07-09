"""Batch E item #10c — R8 no-EOF hang protection.

A misbehaved (or hung) ansible-playbook child can emit a complete event
stream — including the final ``v2_playbook_on_stats`` — and then never
close stdout, never exit. Without R8 the runner's ``_drive`` loop would
keep waiting on ``child.expect(...)`` for as long as the per-read timeout
allows. R8 bounds the post-stats wait with a 30s watchdog: if EOF doesn't
fire within ``_EOF_WATCHDOG_S`` of the stats event, the runner logs a
warning and breaks out of the wait loop as if EOF had arrived.

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

from ansible_aom.ansible.runner import _EOF_WATCHDOG_S


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


@pytest.mark.parametrize(
    "sleep_seconds",
    [120],
)
def test_runner_returns_within_bounded_time_when_child_hangs_after_stats(
    sleep_seconds: int,
) -> None:
    """R8 regression marker: the runner must not wait indefinitely on a
    hung child once the final stats event has been consumed.

    With the post-stats EOF watchdog, ``run_playbook`` returns within
    ``_EOF_WATCHDOG_S`` + a small grace for spawn/cold-start. Without
    R8 this would block until the child eventually exits (never, here).
    """
    from ansible_aom.ansible.runner import run_playbook

    renderer = MagicMock()
    cmd, args = _fake_ansible_hangs_after_stats(
        [
            {"_event": "v2_playbook_on_start", "_timestamp": "2026-05-08T10:00:00Z"},
            {"_event": "v2_playbook_on_stats", "_timestamp": "2026-05-08T10:00:01Z"},
        ],
        sleep_seconds=sleep_seconds,
    )

    result: dict[str, int | None] = {"exit_code": None}

    def _drive_runner() -> None:
        with patch("ansible_aom.ansible.runner._build_command", return_value=(cmd, args)):
            # Tight per-read timeout keeps the pre-stats wait short;
            # the post-stats watchdog is what bounds the run as a whole.
            result["exit_code"] = run_playbook("playbook.yml", [], renderer, timeout=0.5)

    worker = threading.Thread(target=_drive_runner, daemon=True)
    worker.start()

    # Budget: _EOF_WATCHDOG_S + 10s slack for spawn, child cleanup
    # (SIGKILL + waitpid), and post-loop renderer/sink finalisation.
    # Any regression that disables the watchdog makes this timeout.
    budget = _EOF_WATCHDOG_S + 10.0
    worker.join(timeout=budget)

    if worker.is_alive():
        pytest.fail(
            f"run_playbook did not return within {budget:.1f}s after the child "
            "stopped emitting events — R8 EOF watchdog did not fire"
        )
    assert result["exit_code"] is not None

    # The watchdog warning must be visible to the user via print_log
    # so an operator staring at a hung run knows AOM bailed out, not
    # the child.
    printed = [c.args[0] for c in renderer.print_log.call_args_list]
    assert any("EOF" in line and "watchdog" in line.lower() for line in printed), (
        f"expected EOF watchdog warning, got: {printed!r}"
    )


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
    with patch(
        "ansible_aom.ansible.runner._build_command", return_value=(sys.executable, ["-c", code])
    ):
        exit_code = run_playbook("playbook.yml", [], renderer, timeout=0.5)
    elapsed = time.monotonic() - start

    assert exit_code == 0
    assert elapsed < 5.0, f"clean EOF should be sub-5s, took {elapsed:.2f}s"
